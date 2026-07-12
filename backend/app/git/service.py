from pathlib import Path

from git import InvalidGitRepositoryError, Repo
from loguru import logger

from app.config import get_knowledge_path


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
    logger.info("Git initialized: KB {}", knowledge_id)
    return True


def get_git_log(knowledge_id: str, limit: int = 10, file_path: str | None = None) -> list[dict]:
    """获取Git提交历史"""
    repo = _get_repo(knowledge_id)
    if not repo:
        logger.warning("Git repo not found: KB {}", knowledge_id)
        return []

    try:
        commits = []
        kwargs = {"max_count": limit}
        if file_path:
            kwargs["paths"] = [file_path]
        for commit in repo.iter_commits(**kwargs):
            commits.append({
                "hash": commit.hexsha,
                "author": commit.author.name,
                "email": commit.author.email,
                "date": commit.committed_datetime.isoformat(),
                "message": commit.message.strip(),
            })
        logger.debug("Git log: KB {}, {} commits", knowledge_id, len(commits))
        return commits
    except (ValueError, TypeError):
        return []
    finally:
        repo.close()


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
            diff = repo.commit(commit).diff(None)
            if file_path:
                diff = [d for d in diff if d.a_path == file_path or d.b_path == file_path]
            return "\n".join(str(d) for d in diff)
        else:
            diff = repo.index.diff(None)
            if file_path:
                diff = [d for d in diff if d.a_path == file_path or d.b_path == file_path]
            return "\n".join(str(d) for d in diff)
    except Exception:
        return ""
    finally:
        repo.close()


def get_file_at_commit(knowledge_id: str, commit_hash: str, file_path: str) -> str | None:
    """获取指定提交的文件内容"""
    repo = _get_repo(knowledge_id)
    if not repo:
        return None
    try:
        commit = repo.commit(commit_hash)
        return commit.tree[file_path].data_stream.read().decode("utf-8")
    except (KeyError, Exception):
        return None
    finally:
        repo.close()


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
            full_path = get_knowledge_path(knowledge_id) / file_path
            if not full_path.exists():
                return None
            repo.index.add([file_path])
        else:
            repo.index.add(".")

        repo.index.commit(message)
        logger.info("Git committed in KB {}, msg={}", knowledge_id, message)
    except Exception as e:
        logger.error("Git commit failed: KB {}, {}", knowledge_id, e)
        return None
    finally:
        repo.close()

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
        repo.git.revert("--no-edit", commit_hash)
        logger.info("Git reverted: {} in KB {}", commit_hash[:8], knowledge_id)
        return True
    except Exception:
        try:
            repo.git.checkout(commit_hash, "--", ".")
            repo.index.commit(f"Revert to {commit_hash[:8]}")
            logger.info("Git reverted (checkout): {} in KB {}", commit_hash[:8], knowledge_id)
            return True
        except Exception:
            logger.error("Git revert failed: KB {}, {}", knowledge_id, commit_hash)
            return False
    finally:
        repo.close()
