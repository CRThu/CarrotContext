from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount

from app.mcp.auth import set_mcp_user
from app.mcp.tools import mcp


class MCPAuthMiddleware:
    """Middleware to extract and validate JWT token from MCP requests"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract Authorization header
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()

            token = None
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]

            # Set the current user context
            await set_mcp_user(token)

        return await self.app(scope, receive, send)


# 创建MCP ASGI应用
mcp_app = Starlette(
    routes=[
        Mount("/", app=mcp.sse_app()),
    ],
    middleware=[Middleware(MCPAuthMiddleware)],
)
