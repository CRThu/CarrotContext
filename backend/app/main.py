from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings, ensure_directories
from app.database import init_db
from app.auth.router import router as auth_router
from app.knowledge.router import router as knowledge_router
from app.lock.router import router as lock_router
from app.search.router import router as search_router
from app.git.router import router as git_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    ensure_directories()
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["知识管理"])
app.include_router(lock_router, prefix="/api/lock", tags=["文件锁定"])
app.include_router(search_router, prefix="/api/search", tags=["搜索"])
app.include_router(git_router, prefix="/api/git", tags=["Git版本控制"])

# MCP路由
if settings.MCP_ENABLED:
    from app.mcp.server import mcp_app
    app.mount(settings.MCP_PATH, mcp_app)


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME} v{settings.APP_VERSION}"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
