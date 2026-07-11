from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "CarrotContext"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # 数据库配置
    DATABASE_PATH: Path = Path("./data/carrotcontext.db")

    # JWT配置
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30

    # 知识库存储路径
    KNOWLEDGE_BASE_PATH: Path = Path("./data/knowledge")

    # 文件锁定配置
    LOCK_TIMEOUT_MINUTES: int = 30
    LOCK_CLEANUP_INTERVAL_MINUTES: int = 5

    # CORS配置
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # MCP配置
    MCP_ENABLED: bool = True
    MCP_PATH: str = "/mcp"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()


def get_knowledge_path(knowledge_id: str) -> Path:
    """获取知识库的文件系统路径"""
    return settings.KNOWLEDGE_BASE_PATH / knowledge_id


def ensure_directories():
    """确保必要的目录存在"""
    settings.KNOWLEDGE_BASE_PATH.mkdir(parents=True, exist_ok=True)
    settings.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
