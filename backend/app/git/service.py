import subprocess
from pathlib import Path
from app.config import settings


def get_knowledge_path(knowledge_id: str) -> Path:
    return settings.KNOWLEDGE_BASE_PATH / knowledge_id


def init_git(knowledge_id: str) -> bool:
    knowledge_path = get_knowledge_path(knowledge_id)
    if not knowledge_path.exists():
        return False
    git_dir = knowledge_path / ".git"
    if git_dir.exists():
        return True
    subprocess.run(["git", "init"], cwd=str(knowledge_path), capture_output=True)
    subprocess.run(["git", "config", "user.email", "carrotcontext@local"], cwd=str(knowledge_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "CarrotContext"], cwd=str(knowledge_path), capture_output=True)
    return True


def get_git_log(knowledge_id: str, limit: int = 10) -> list[dict]:
    knowledge_path = get_knowledge_path(knowledge_id)
    if not (knowledge_path / ".git").exists():
        return []

    result = subprocess.run(
        ["git", "log", f"--max-count={limit}", "--format=%H|%an|%ae|%ai|%s"],
        cwd=str(knowledge_path),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []

    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 4)
        if len(parts) == 5:
            commits.append({
                "hash": parts[0],
                "author": parts[1],
                "email": parts[2],
                "date": parts[3],
                "message": parts[4],
            })
    return commits


def get_git_diff(knowledge_id: str, file_path: str | None = None, commit: str | None = None) -> str:
    knowledge_path = get_knowledge_path(knowledge_id)
    if not (knowledge_path / ".git").exists():
        return ""

    cmd = ["git", "diff"]
    if commit:
        cmd = ["git", "diff", commit]
    if file_path:
        cmd.append(file_path)

    result = subprocess.run(cmd, cwd=str(knowledge_path), capture_output=True, text=True)
    return result.stdout


def create_git_commit(knowledge_id: str, message: str, file_path: str | None = None) -> dict | None:
    knowledge_path = get_knowledge_path(knowledge_id)
    if not (knowledge_path / ".git").exists():
        init_git(knowledge_id)

    if file_path:
        subprocess.run(["git", "add", file_path], cwd=str(knowledge_path), capture_output=True)
    else:
        subprocess.run(["git", "add", "."], cwd=str(knowledge_path), capture_output=True)

    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=str(knowledge_path),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return None

    log = get_git_log(knowledge_id, 1)
    return log[0] if log else None


def revert_git_commit(knowledge_id: str, commit_hash: str) -> bool:
    knowledge_path = get_knowledge_path(knowledge_id)
    if not (knowledge_path / ".git").exists():
        return False

    result = subprocess.run(
        ["git", "revert", "--no-edit", commit_hash],
        cwd=str(knowledge_path),
        capture_output=True,
        text=True,
    )
    return result.returncode == 0
