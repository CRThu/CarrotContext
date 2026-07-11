<div align="center">

# CarrotContext

一个基于文件系统的企业知识库管理系统

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge)](LICENSE)

</div>

---

## 功能特性

| 功能 | 说明 |
|:---:|:---|
|  | **知识库管理** - 创建、浏览、删除知识库，支持分类和标签 |
|  | **文件树浏览** - 支持文件夹展开/折叠的树形结构 |
|  | **文件拖拽移动** - 支持文件拖拽到文件夹进行移动 |
|  | **文件上传** - 支持图片、PDF、压缩包等二进制文件上传 |
|  | **Markdown 预览** - 实时渲染，支持表格、代码高亮 |
|  | **代码编辑器** - VSCode 风格的 Monaco Editor |
|  | **JWT 认证** - 安全的用户登录系统 |
|  | **用户管理** - 管理员角色，用户注册、角色修改、删除 |
|  | **权限管理** - 知识库级别权限（admin/editor/viewer） |
|  | **知识库属性** - 查看和编辑知识库元数据 |
|  | **文件锁定** - 悲观锁防止多人同时编辑冲突 |
|  | **Git 集成** - 使用 GitPython 进行版本控制 |
|  | **Git 历史查看** - 查看提交历史、差异对比、版本回滚 |
|  | **全文搜索** - BM25 元数据搜索 + 文件内容搜索 |
|  | **主题切换** - 浅色/深色/跟随系统三种模式 |
|  | **MCP 服务** - SSE 协议，支持外部 Agent 访问 |

## 页面展示

### 登录页面

现代化登录卡片设计，搭配渐变按钮与柔和背景装饰。

<div align="center">
<img src="docs/images/login.png" alt="登录页面" width="600">
</div>

### 知识库列表

Notion 风格的侧边栏分类导航，支持按类别折叠展开知识库。

<div align="center">
<img src="docs/images/dashboard.png" alt="知识库列表" width="600">
</div>

### 知识库详情

Notion 风格的左右分栏布局，左侧文件目录树 + 右侧白纸画布。

<div align="center">
<img src="docs/images/knowledge-detail.png" alt="知识库详情" width="600">
</div>

### Markdown 预览

支持表格、代码高亮等丰富内容的实时渲染预览。

<div align="center">
<img src="docs/images/markdown-preview.png" alt="Markdown预览" width="600">
</div>

### 代码预览

语法高亮的代码文件只读预览视图。

<div align="center">
<img src="docs/images/code-preview.png" alt="代码预览" width="600">
</div>

### 代码编辑器

VSCode 风格的 Monaco Editor 代码编辑体验。

<div align="center">
<img src="docs/images/code-editor.png" alt="代码编辑器" width="600">
</div>

## 技术栈

<div align="center">

**后端**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![GitPython](https://img.shields.io/badge/GitPython-F05032?style=for-the-badge&logo=git&logoColor=white)

**前端**

![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)

**核心依赖**

![jieba](https://img.shields.io/badge/jieba-中文分库-999999?style=for-the-badge)
![rank-bm25](https://img.shields.io/badge/rank--bm25-搜索排序-999999?style=for-the-badge)
![python-jose](https://img.shields.io/badge/python--jose-JWT-999999?style=for-the-badge)
![MCP](https://img.shields.io/badge/MCP-Agent协议-999999?style=for-the-badge)

</div>

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- Bun (推荐) 或 npm
- Git

### 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/CarrotContext.git
cd CarrotContext

# 后端
cd backend
uv sync

# 前端
cd ../frontend
bun install
```

### 启动

```bash
# 后端 (终端1)
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端 (终端2)
cd frontend
bun dev
```

访问 http://localhost:5173

### Docker 部署

使用 Docker Compose + Caddy 一键部署：

```bash
# 克隆仓库
git clone https://github.com/your-username/CarrotContext.git
cd CarrotContext

# 配置环境变量（可选）
export JWT_SECRET_KEY=your-production-secret-key
export APP_PORT=80              # 自定义前端端口（默认 80）

# 启动服务
docker-compose up -d
```

**服务架构**

```
用户请求
    │
    ▼
┌─────────────────────────────────────┐
│  Caddy (:${APP_PORT})               │
│  ├─ /           → 静态资源 (dist/)  │
│  ├─ /api/*      → Backend:8000      │
│  └─ /mcp/*      → Backend:8000      │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│  Backend (内部 :8000)               │
│  ├─ FastAPI REST API                │
│  ├─ MCP SSE 服务                    │
│  └─ SQLite + 文件系统               │
└─────────────────────────────────────┘
```

**MCP 服务**

MCP (Model Context Protocol) 服务通过 SSE 协议提供，支持外部 Agent 访问知识库：

- SSE 端点: `http://localhost/mcp/sse`
- 提供工具: `list_knowledge_base`, `get_knowledge_detail`, `read_file_content`, `update_file`, `create_new_knowledge`, `search_knowledge`, `get_git_history`, `get_file_diff`, `commit_changes`

**数据持久化**

知识库数据存储在 `./data/` 目录：
- `./data/knowledge/` - 知识库文件
- `./data/carrotcontext.db` - SQLite 数据库

停止服务：

```bash
docker-compose down

# 停止并删除数据
docker-compose down -v
rm -rf ./data
```

## 项目结构

```
CarrotContext/
├── backend/                    # Python 后端
│   ├── app/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # SQLite 管理
│   │   ├── auth/              # 认证模块（注册、登录、用户管理）
│   │   ├── knowledge/         # 知识管理（CRUD + 权限）
│   │   ├── files/             # 文件操作（读写、移动、上传、下载）
│   │   ├── lock/              # 文件锁定
│   │   ├── search/            # 搜索功能
│   │   ├── git/               # Git 集成
│   │   └── mcp/               # MCP 服务（SSE + 认证）
│   ├── tests/
│   └── pyproject.toml
├── frontend/                  # React 前端
│   ├── src/
│   │   ├── components/        # 组件
│   │   ├── pages/             # 页面
│   │   ├── stores/            # 状态管理
│   │   └── lib/               # 工具函数
│   ├── Caddyfile              # Caddy 配置
│   └── tests/
├── docs/images/               # 文档图片
├── docker-compose.yml
└── .github/workflows/ci.yml  # GitHub Actions CI
```

## API 文档

启动后访问: http://localhost:8000/docs

### 认证 API

| 方法 | 路径 | 说明 |
|:---:|:---|:---|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录，返回 JWT token |
| GET | `/api/auth/me` | 获取当前用户信息 |
| GET | `/api/auth/users` | 用户列表（管理员） |
| PUT | `/api/auth/users/{id}/role` | 修改用户角色（管理员） |
| DELETE | `/api/auth/users/{id}` | 删除用户（管理员） |

### 知识库 API

| 方法 | 路径 | 说明 |
|:---:|:---|:---|
| GET | `/api/knowledge` | 获取知识库列表 |
| POST | `/api/knowledge` | 创建知识库 |
| GET | `/api/knowledge/{id}` | 获取知识库详情 |
| PUT | `/api/knowledge/{id}` | 更新知识库信息 |
| DELETE | `/api/knowledge/{id}` | 删除知识库 |
| GET | `/api/knowledge/{id}/tree` | 获取文件树 |
| GET | `/api/knowledge/{id}/files/{path}` | 获取文件内容 |
| PUT | `/api/knowledge/{id}/files/{path}` | 更新文件内容 |
| POST | `/api/knowledge/{id}/files/move` | 移动文件 |
| POST | `/api/knowledge/{id}/files/upload` | 上传文件 |
| GET | `/api/knowledge/{id}/files/{path}/raw` | 下载二进制文件 |
| POST | `/api/knowledge/{id}/dirs` | 创建目录 |
| GET | `/api/knowledge/{id}/permissions` | 权限列表（管理员） |
| POST | `/api/knowledge/{id}/permissions` | 设置权限（管理员） |
| DELETE | `/api/knowledge/{id}/permissions/{rule_id}` | 删除权限（管理员） |

### 搜索 API

| 方法 | 路径 | 说明 |
|:---:|:---|:---|
| GET | `/api/search?q={query}` | 全局搜索（支持 mode: all/metadata/content） |

### 文件锁定 API

| 方法 | 路径 | 说明 |
|:---:|:---|:---|
| POST | `/api/lock` | 获取文件锁 |
| DELETE | `/api/lock` | 释放文件锁 |
| GET | `/api/lock/status` | 查询锁状态 |

### Git API

| 方法 | 路径 | 说明 |
|:---:|:---|:---|
| POST | `/api/git/{id}/init` | 初始化 Git 仓库 |
| GET | `/api/git/{id}/log` | 获取提交历史 |
| GET | `/api/git/{id}/diff` | 获取文件差异 |
| POST | `/api/git/{id}/commit` | 创建提交 |
| POST | `/api/git/{id}/revert` | 回滚提交 |

### 其他

| 方法 | 路径 | 说明 |
|:---:|:---|:---|
| GET | `/` | API 欢迎信息 |
| GET | `/health` | 健康检查 |
| GET | `/mcp/sse` | MCP SSE 服务端点（支持可选JWT认证） |

## 配置

### 后端环境变量

创建 `backend/.env` 文件:

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_PATH` | `./data/carrotcontext.db` | 数据库路径 |
| `JWT_SECRET_KEY` | `your-secret-key-change-in-production` | JWT 密钥 |
| `JWT_ALGORITHM` | `HS256` | JWT 算法 |
| `JWT_EXPIRE_MINUTES` | `30` | Token 过期时间 |
| `KNOWLEDGE_BASE_PATH` | `./data/knowledge` | 知识库存储路径 |
| `LOCK_TIMEOUT_MINUTES` | `30` | 文件锁超时时间 |
| `CORS_ORIGINS` | `["http://localhost:5173", "http://localhost:3000"]` | 允许的跨域来源 |
| `MCP_ENABLED` | `true` | 是否启用 MCP 服务 |
| `MCP_PATH` | `/mcp` | MCP 挂载路径 |

### Docker 环境变量

在 `docker-compose.yml` 或 `.env` 中配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_PORT` | `80` | 前端访问端口 |
| `JWT_SECRET_KEY` | `your-secret-key-change-in-production` | JWT 密钥 |

### 前端开发配置

创建 `frontend/.env` 文件:

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `VITE_API_URL` | `http://localhost:8000` | 后端 API 地址 |

## 测试

```bash
# 后端测试
cd backend
uv run pytest

# 前端测试
cd frontend
npx vitest run

# E2E 测试
cd frontend
npx playwright test
```

## License

[Apache License 2.0](LICENSE)
