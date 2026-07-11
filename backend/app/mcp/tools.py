from mcp.server.fastmcp import FastMCP

from app.files.service import get_file_content, update_file_content
from app.git.service import create_git_commit, get_git_diff, get_git_log
from app.knowledge.permissions import check_access
from app.knowledge.service import (
    create_knowledge,
    get_knowledge,
    list_knowledge,
)
from app.mcp.auth import get_mcp_user
from app.search.service import search_content, search_metadata

mcp = FastMCP("CarrotContext")


async def _check_permission(knowledge_id: str, required: str) -> str | None:
    """Check permission and return error message if denied, None if allowed."""
    user = get_mcp_user()
    user_id = user.get("id") if user else None
    has_perm = await check_access(user_id, knowledge_id, required)
    if not has_perm:
        role_name = user.get("role", "anonymous") if user else "anonymous"
        return f"权限不足：当前角色 {role_name}，需要 {required} 或更高权限"
    return None


@mcp.tool()
async def list_knowledge_base() -> str:
    """列出所有知识库"""
    knowledge_list = list_knowledge()
    if not knowledge_list:
        return "没有找到知识库"

    user = get_mcp_user()
    user_id = user.get("id") if user else None
    is_admin = user and user.get("role") == "admin"

    result = []
    for k in knowledge_list:
        if is_admin or await check_access(user_id, k["id"], "read"):
            result.append(
                f"- {k['id']}: {k['name']} ({k.get('description', '')})"
            )

    if not result:
        return "没有找到知识库"
    return "\n".join(result)


@mcp.tool()
async def get_knowledge_detail(knowledge_id: str) -> str:
    """获取知识库详情"""
    perm_error = await _check_permission(knowledge_id, "read")
    if perm_error:
        return perm_error
    knowledge = get_knowledge(knowledge_id)
    if not knowledge:
        return f"知识库 {knowledge_id} 不存在"
    return f"""
ID: {knowledge['id']}
名称: {knowledge['name']}
描述: {knowledge.get('description', '')}
标签: {', '.join(knowledge.get('tags', []))}
创建者: {knowledge['created_by']}
创建时间: {knowledge['created_at']}
更新者: {knowledge['updated_by']}
更新时间: {knowledge['updated_at']}
版本: {knowledge['version']}
"""


@mcp.tool()
async def read_file_content(knowledge_id: str, file_path: str) -> str:
    """读取文件内容"""
    perm_error = await _check_permission(knowledge_id, "read")
    if perm_error:
        return perm_error
    content = get_file_content(knowledge_id, file_path)
    if not content:
        return f"文件 {file_path} 不存在"
    return content["content"]


@mcp.tool()
async def update_file(
    knowledge_id: str, file_path: str, content: str
) -> str:
    """更新文件内容"""
    perm_error = await _check_permission(knowledge_id, "write")
    if perm_error:
        return perm_error
    success = update_file_content(knowledge_id, file_path, content)
    if success:
        return f"文件 {file_path} 更新成功"
    return f"文件 {file_path} 更新失败"


@mcp.tool()
async def create_new_knowledge(
    knowledge_id: str,
    name: str,
    description: str = "",
    tags: str = "",
) -> str:
    """创建新知识库"""
    user = get_mcp_user()
    if user is None or user.get("role") != "admin":
        return "权限不足：只有管理员可以创建新知识库"

    tag_list = (
        [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    )
    try:
        username = user["username"] if user else "mcp_user"
        create_knowledge(
            knowledge_id, name, description, tag_list, username
        )
        return f"知识库 {name} 创建成功"
    except ValueError as e:
        return str(e)


@mcp.tool()
async def search_knowledge(query: str, mode: str = "all") -> str:
    """搜索知识库"""
    user = get_mcp_user()
    user_id = user.get("id") if user else None
    is_admin = user and user.get("role") == "admin"

    results = []
    if mode in ("all", "metadata"):
        metadata_results = search_metadata(query)
        for r in metadata_results:
            kid = r.get("knowledge_id", "")
            if is_admin or await check_access(user_id, kid, "read"):
                title = r.get("title", "")
                summary = r.get("summary", "")[:100]
                results.append(f"[元数据] {kid}: {title} - {summary}")

    if mode in ("all", "content"):
        content_results = search_content(query)
        for r in content_results[:5]:
            file_path = r.get("file", "")
            kid = file_path.split("/")[0] if "/" in file_path else ""
            if not kid or not (is_admin or await check_access(user_id, kid, "read")):
                continue
            line = r.get("line", "")
            content = r.get("content", "")[:100]
            results.append(f"[内容] {file_path}:{line} - {content}")

    if not results:
        return "没有找到相关结果"
    return "\n".join(results)


@mcp.tool()
async def get_git_history(
    knowledge_id: str, limit: int = 10
) -> str:
    """获取Git提交历史"""
    perm_error = await _check_permission(knowledge_id, "read")
    if perm_error:
        return perm_error
    commits = get_git_log(knowledge_id, limit)
    if not commits:
        return "没有提交历史"
    result = []
    for c in commits:
        hash_short = c["hash"][:8]
        result.append(
            f"{hash_short} - {c['message']} ({c['author']}, {c['date']})"
        )
    return "\n".join(result)


@mcp.tool()
async def get_file_diff(
    knowledge_id: str,
    file_path: str = "",
    commit: str = "",
) -> str:
    """获取文件差异"""
    perm_error = await _check_permission(knowledge_id, "read")
    if perm_error:
        return perm_error
    diff = get_git_diff(
        knowledge_id, file_path or None, commit or None
    )
    return diff if diff else "没有差异"


@mcp.tool()
async def commit_changes(
    knowledge_id: str,
    message: str,
    file_path: str = "",
) -> str:
    """提交更改"""
    perm_error = await _check_permission(knowledge_id, "write")
    if perm_error:
        return perm_error
    result = create_git_commit(
        knowledge_id, message, file_path or None
    )
    if result:
        hash_short = result["hash"][:8]
        return f"提交成功: {hash_short} - {result['message']}"
    return "提交失败"
