# CarrotContext - Agent协作指南

## 项目概述

CarrotContext是一个基于文件系统的企业知识库管理系统，支持Markdown/代码文件的浏览、编辑、版本管理，提供Web界面和MCP服务两种访问方式。

## 技术栈

- **后端**: Python 3.11+ / FastAPI / SQLite / uv
- **前端**: React 18 / TypeScript / Vite / Bun
- **测试**: pytest / Vitest / Playwright
- **部署**: Docker / docker-compose

## 项目结构

```
carrotcontext/
├── backend/                    # Python后端
│   ├── app/
│   │   ├── main.py            # FastAPI入口
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # SQLite管理
│   │   ├── auth/              # 认证模块
│   │   ├── knowledge/         # 知识管理
│   │   ├── lock/              # 文件锁定
│   │   ├── search/            # 搜索功能
│   │   ├── git/               # Git集成
│   │   └── mcp/               # MCP服务
│   ├── tests/
│   └── pyproject.toml
├── frontend/                  # Vite + React前端
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── stores/
│   │   └── lib/
│   ├── tests/
│   ├── e2e/
│   └── package.json
├── data/                      # 知识库存储
│   └── knowledge/
└── agents.md                  # 本文件
```

## 开发约定

### 代码风格
- Python: 使用ruff格式化，遵循PEP 8
- TypeScript: 使用ESLint + Prettier
- 提交信息: 遵循Conventional Commits规范

### Git工作流
- main: 生产分支
- develop: 开发分支
- feature/*: 功能分支
- fix/*: 修复分支

### 测试要求
- 后端: pytest覆盖率 > 80%
- 前端: Vitest覆盖率 > 70%
- E2E: 覆盖核心用户流程

## 核心模块说明

### 认证模块 (auth)
- JWT token认证
- 用户注册/登录
- 密码使用bcrypt哈希

### 知识管理 (knowledge)
- 文件系统存储，每个根节点有.manifest.json
- 支持文件/目录的CRUD操作
- 文件上传支持

### 文件锁定 (lock)
- 悲观锁实现，基于.lock文件
- 支持锁状态查询和超时处理

### 搜索 (search)
- 元数据搜索: BM25算法 + SQLite索引
- 内容搜索: ripgrep全文搜索

### Git集成 (git)
- 使用GitPython进行版本控制
- 支持提交历史、差异查看、版本回滚

### MCP服务 (mcp)
- Streamable HTTP协议
- 提供知识库访问工具

## 环境变量

```env
# 后端
DATABASE_URL=sqlite:///./data/carrotcontext.db
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# 前端
VITE_API_URL=http://localhost:8000
```

## 常用命令

```bash
# 后端
cd backend
uv sync                          # 安装依赖
uv run uvicorn app.main:app --reload  # 启动开发服务器
uv run pytest                    # 运行测试

# 前端
cd frontend
bun install                      # 安装依赖
bun dev                          # 启动开发服务器
bun test                         # 运行测试
bunx playwright test             # E2E测试
```

## 注意事项

1. 知识库存储在data/knowledge/目录下，每个知识库是独立的文件夹
2. 每个知识库根目录有.manifest.json存储元数据
3. 文件锁定使用.lock文件，编辑前需要获取锁
4. Git版本控制为每个知识库独立初始化
5. MCP服务挂载在/mcp路径，支持远程访问
