# CarrotContext Backend

企业知识库管理系统后端 (Python 3.12+)

## 安装

```bash
uv sync
```

## 运行

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 测试

```bash
uv run pytest
```

## 代码检查

```bash
uv run ruff check .
uv run ruff format .
```

## 项目结构

```
app/
├── main.py            # FastAPI 入口
├── config.py          # 配置管理（pydantic-settings）
├── database.py        # SQLite 数据库管理
├── auth/              # JWT 认证模块
│   ├── router.py      # API 路由
│   ├── service.py     # 业务逻辑
│   └── models.py      # 数据模型
├── knowledge/         # 知识库管理
│   ├── router.py
│   ├── service.py
│   ├── manifest.py    # manifest.json 管理
│   └── models.py
├── lock/              # 文件锁定
│   ├── router.py
│   ├── service.py
│   └── models.py
├── search/            # 搜索功能
│   ├── router.py
│   └── service.py     # ripgrep + Python grep fallback
├── git/               # Git 集成（GitPython）
│   ├── router.py
│   ├── service.py
│   └── models.py
└── mcp/               # MCP 服务（SSE 协议）
    ├── server.py
    └── tools.py
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DATABASE_URL | sqlite+aiosqlite:///./data/carrotcontext.db | 数据库路径 |
| JWT_SECRET_KEY | your-secret-key | JWT 密钥 |
| JWT_ALGORITHM | HS256 | JWT 算法 |
| JWT_EXPIRE_MINUTES | 30 | Token 过期时间 |
| KNOWLEDGE_BASE_PATH | ./data/knowledge | 知识库存储路径 |
| CORS_ORIGINS | ["http://localhost:5173"] | 允许的跨域来源 |
| MCP_ENABLED | true | 是否启用 MCP |
| MCP_PATH | /mcp | MCP 挂载路径 |

## Docker

```bash
docker build -t carrotcontext-backend .
docker run -p 8000:8000 -v ./data:/app/data carrotcontext-backend
```
