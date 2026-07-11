"""MCP authentication helper"""
from contextvars import ContextVar

from app.auth.service import decode_token, get_user_by_id

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
