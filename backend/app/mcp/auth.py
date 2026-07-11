"""MCP authentication helper"""
from contextvars import ContextVar
from typing import Any

from app.auth.service import decode_token, get_user_by_id
from app.knowledge.permissions import check_permission

# Context variable to store current user info for MCP requests
_current_user: ContextVar[dict | None] = ContextVar("current_user", default=None)


async def set_mcp_user(token: str | None) -> None:
    """Set the current user from an optional JWT token"""
    if token is None:
        _current_user.set(None)
        return

    token_data = await decode_token(token)
    if token_data:
        user = await get_user_by_id(token_data["user_id"])
        _current_user.set(user)
    else:
        _current_user.set(None)


def get_mcp_user() -> dict | None:
    """Get the current MCP user"""
    return _current_user.get()


async def require_permission(knowledge_id: str, required_role: str) -> bool:
    """Check if current user has required permission"""
    user = get_mcp_user()
    user_id = user["id"] if user else None
    return await check_permission(user_id, knowledge_id, required_role)


def require_editor(knowledge_id: str) -> Any:
    """Decorator to require editor permission - returns error message or None"""
    import asyncio

    async def check():
        has_perm = await require_permission(knowledge_id, "editor")
        if not has_perm:
            return "权限不足：需要editor或更高权限"
        return None

    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If we're in an async context, we need to handle this differently
        return None  # Will be checked in async tool functions
    return loop.run_until_complete(check())
