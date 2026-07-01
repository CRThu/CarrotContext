from mcp.server.fastmcp import FastMCP
from app.knowledge.service import (
    list_knowledge,
    get_knowledge,
    get_file_content,
    update_file_content,
    create_knowledge,
)
from app.search.service import search_metadata, search_content
from app.git.service import get_git_log, get_git_diff, create_git_commit

mcp = FastMCP("CarrotContext")


@mcp.tool()
def list_knowledge_base() -> str:
    """列出所有知识库"""
    knowledge_list = list_knowledge()
    if not knowledge_list:
        return "没有找到知识库"
    result = []
    for k in knowledge_list:
        result.append(f"- {k['id']}: {k['name']} ({k.get('description', '')})")
    return "\n".join(result)


@mcp.tool()
def get_knowledge_detail(knowledge_id: str) -> str:
    """获取知识库详情"""
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
def read_file_content(knowledge_id: str, file_path: str) -> str:
    """读取文件内容"""
    content = get_file_content(knowledge_id, file_path)
    if not content:
        return f"文件 {file_path} 不存在"
    return content["content"]


@mcp.tool()
def update_file(knowledge_id: str, file_path: str, content: str) -> str:
    """更新文件内容"""
    success = update_file_content(knowledge_id, file_path, content)
    if success:
        return f"文件 {file_path} 更新成功"
    return f"文件 {file_path} 更新失败"


@mcp.tool()
def create_new_knowledge(knowledge_id: str, name: str, description: str = "", tags: str = "") -> str:
    """创建新知识库"""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    try:
        create_knowledge(knowledge_id, name, description, tag_list, "mcp_user")
        return f"知识库 {name} 创建成功"
    except ValueError as e:
        return str(e)


@mcp.tool()
def search_knowledge(query: str, mode: str = "all") -> str:
    """搜索知识库"""
    results = []
    if mode in ("all", "metadata"):
        metadata_results = search_metadata(query)
        for r in metadata_results:
            results.append(f"[元数据] {r.get('knowledge_id')}: {r.get('title')} - {r.get('summary', '')[:100]}")

    if mode in ("all", "content"):
        content_results = search_content(query)
        for r in content_results[:5]:
            results.append(f"[内容] {r.get('file')}:{r.get('line')} - {r.get('content', '')[:100]}")

    if not results:
        return "没有找到相关结果"
    return "\n".join(results)


@mcp.tool()
def get_git_history(knowledge_id: str, limit: int = 10) -> str:
    """获取Git提交历史"""
    commits = get_git_log(knowledge_id, limit)
    if not commits:
        return "没有提交历史"
    result = []
    for c in commits:
        result.append(f"{c['hash'][:8]} - {c['message']} ({c['author']}, {c['date']})")
    return "\n".join(result)


@mcp.tool()
def get_file_diff(knowledge_id: str, file_path: str = "", commit: str = "") -> str:
    """获取文件差异"""
    diff = get_git_diff(knowledge_id, file_path or None, commit or None)
    return diff if diff else "没有差异"


@mcp.tool()
def commit_changes(knowledge_id: str, message: str, file_path: str = "") -> str:
    """提交更改"""
    result = create_git_commit(knowledge_id, message, file_path or None)
    if result:
        return f"提交成功: {result['hash'][:8]} - {result['message']}"
    return "提交失败"
