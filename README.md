<div align="center">

# CarrotContext

一个基于文件系统的企业知识库管理系统

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge)](LICENSE)

</div>

---

## ✨ 功能特性

| 功能 | 说明 |
|:---:|:---|
| 📚 | **知识库管理** - 创建、浏览、删除知识库 |
| 🌲 | **文件树浏览** - 支持文件夹展开/折叠的树形结构 |
| 📝 | **Markdown 预览** - 实时渲染，支持表格、代码高亮 |
| 💻 | **代码编辑器** - VSCode 风格的 Monaco Editor |
| 🔐 | **JWT 认证** - 安全的用户登录系统 |
| 🔒 | **文件锁定** - 悲观锁防止多人同时编辑冲突 |
| 🔄 | **Git 集成** - 版本控制、提交历史、差异对比 |
| 🔍 | **全文搜索** - BM25 元数据搜索 + ripgrep 内容搜索 |
| 🤖 | **MCP 服务** - Streamable HTTP 协议，支持外部 Agent 访问 |

## 📸 页面展示

### 登录页面

<div align="center">
<img src="docs/images/login.png" alt="登录页面" width="600">
</div>

### 主页面

<div align="center">
<img src="docs/images/dashboard.png" alt="主页面" width="600">
</div>

### 知识库详情

<div align="center">
<img src="docs/images/knowledge-detail.png" alt="知识库详情" width="600">
</div>

### Markdown 预览

<div align="center">
<img src="docs/images/markdown-preview.png" alt="Markdown 预览" width="600">
</div>

### 代码编辑器

<div align="center">
<img src="docs/images/code-editor.png" alt="代码编辑器" width="600">
</div>

### 代码预览

<div align="center">
<img src="docs/images/code-preview.png" alt="代码预览" width="600">
</div>

## 🛠️ 技术栈

<div align="center">

**后端**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

**前端**

![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)

</div>

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Bun (推荐) 或 npm

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

### Docker

```bash
docker-compose up -d
```

## 📁 项目结构

```
CarrotContext/
├── backend/                    # Python 后端
│   ├── app/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── auth/              # 认证模块
│   │   ├── knowledge/         # 知识管理
│   │   ├── lock/              # 文件锁定
│   │   ├── search/            # 搜索功能
│   │   ├── git/               # Git 集成
│   │   └── mcp/               # MCP 服务
│   └── tests/
├── frontend/                  # React 前端
│   ├── src/
│   │   ├── components/        # 组件
│   │   ├── pages/             # 页面
│   │   └── stores/            # 状态管理
│   └── tests/
├── docs/images/               # 文档图片
└── docker-compose.yml
```

## 📚 API 文档

启动后访问: http://localhost:8000/docs

| 方法 | 路径 | 说明 |
|:---:|:---|:---|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/knowledge` | 获取知识库列表 |
| POST | `/api/knowledge` | 创建知识库 |
| GET | `/api/knowledge/{id}/tree` | 获取文件树 |
| GET | `/api/knowledge/{id}/file/{path}` | 获取文件内容 |
| PUT | `/api/knowledge/{id}/file/{path}` | 更新文件内容 |
| POST | `/api/search` | 搜索 |

## ⚙️ 配置

创建 `.env` 文件:

```env
DATABASE_URL=sqlite:///./data/carrotcontext.db
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
VITE_API_URL=http://localhost:8000
```

## 📄 License

[Apache License 2.0](LICENSE)
