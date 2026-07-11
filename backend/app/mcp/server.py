from starlette.applications import Starlette
from starlette.routing import Mount

from app.mcp.tools import mcp

# 创建MCP ASGI应用
mcp_app = Starlette(
    routes=[
        Mount("/", app=mcp.sse_app()),
    ],
)
