from pathlib import Path

from git import InvalidGitRepositoryError, Repo

from app.config import settings


def get_knowledge_path(knowledge_id: str) -> Path:
    return settings.KNOWLEDGE_BASE_PATH / knowledge_id


def _get_repo(knowledge_id: str) -> Repo | None:
    """获取Git仓库对象"""
    knowledge_path = get_knowledge_path(knowledge_id)
    if not knowledge_path.exists():
        return None
    try:
        return Repo(knowledge_path)
    except InvalidGitRepositoryError:
        return None


def init_git(knowledge_id: str) -> bool:
    """初始化Git仓库"""
    knowledge_path = get_knowledge_path(knowledge_id)
    if not knowledge_path.exists():
        return False
    git_dir = knowledge_path / ".git"
    if git_dir.exists():
        return True
    repo = Repo.init(knowledge_path)
    repo.config_writer().set_value("user", "email", "carrotcontext@local").release()
    repo.config_writer().set_value("user", "name", "CarrotContext").release()
    return True


def get_git_log(knowledge_id: str, limit: int = 10) -> list[dict]:
    """获取Git提交历史"""
    repo = _get_repo(knowledge_id)
    if not repo:
        return []

    commits = []
    try:
        for commit in repo.iter_commits(max_count=limit):
            commits.append({
                "hash": commit.hexsha,
                "author": commit.author.name,
                "email": commit.author.email,
                "date": commit.committed_datetime.isoformat(),
                "message": commit.message.strip(),
            })
    except (ValueError, TypeError):
        # 空仓库没有提交历史
        pass
    return commits


def get_git_diff(
    knowledge_id: str,
    file_path: str | None = None,
    commit: str | None = None,
) -> str:
    """获取文件差异"""
    repo = _get_repo(knowledge_id)
    if not repo:
        return ""

    try:
        if commit:
            # 比较指定提交与当前工作区
            diff = repo.commit(commit).diff(None)
            if file_path:
                diff = [d for d in diff if d.a_path == file_path or d.b_path == file_path]
            return "\n".join(str(d) for d in diff)
        else:
            # 比较暂存区与工作区
            diff = repo.index.diff(None)
            if file_path:
                diff = [d for d in diff if d.a_path == file_path or d.b_path == file_path]
            return "\n".join(str(d) for d in diff)
    except Exception:
        return ""


def create_git_commit(
    knowledge_id: str,
    message: str,
    file_path: str | None = None,
) -> dict | None:
    """创建Git提交"""
    repo = _get_repo(knowledge_id)
    if not repo:
        init_git(knowledge_id)
        repo = _get_repo(knowledge_id)
        if not repo:
            return None

    try:
        if file_path:
            # 检查文件是否存在
            full_path = get_knowledge_path(knowledge_id) / file_path
            if not full_path.exists():
                return None
            repo.index.add([file_path])
        else:
            repo.index.add(".")

        repo.index.commit(message)
    except Exception:
        return None

    log = get_git_log(knowledge_id, 1)
    return log[0] if log else None


def revert_git_commit(
    knowledge_id: str, commit_hash: str
) -> bool:
    """回滚Git提交"""
    repo = _get_repo(knowledge_id)
    if not repo:
        return False

    try:
        # 使用 git 命令行执行 revert
        repo.git.revert("--no-edit", commit_hash)
        return True
    except Exception:
        # 如果 revert 失败，尝试回退到该提交
        try:
            repo.git.checkout(commit_hash, "--", ".")
            repo.index.commit(f"Revert to {commit_hash[:8]}")
            return True
        except Exception:
            return False
