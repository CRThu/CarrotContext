# CarrotContext - Agent协作指南

## 项目概述

CarrotContext是一个基于文件系统的企业知识库管理系统，支持Markdown/代码文件的浏览、编辑、版本管理，提供Web界面和MCP服务两种访问方式。

## 技术栈

- **后端**: Python 3.12+ / FastAPI / SQLite / uv
- **前端**: React 19 / TypeScript / Vite / Bun / Tailwind CSS 4
- **测试**: pytest / Vitest
- **部署**: Docker / Caddy / docker-compose
- **核心库**: GitPython / python-jose / rank-bm25 / jieba / MCP SDK

## 项目结构

```
carrotcontext/
├── backend/                    # Python后端
│   ├── app/
│   │   ├── main.py            # FastAPI入口
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # SQLite管理
│   │   ├── auth/              # 认证模块
│   │   │   ├── router.py      # 认证路由（注册、登录、用户管理）
│   │   │   ├── service.py     # JWT、密码哈希
│   │   │   └── models.py      # 数据模型
│   │   ├── knowledge/         # 知识管理
│   │   │   ├── router.py      # KB CRUD + 权限管理
│   │   │   ├── service.py     # manifest读写
│   │   │   ├── manifest.py    # manifest文件操作
│   │   │   ├── models.py      # 数据模型
│   │   │   └── permissions.py # 权限检查服务
│   │   ├── files/             # 文件操作
│   │   │   ├── router.py      # 文件读写、移动、上传、下载
│   │   │   └── service.py     # 文件操作服务
│   │   ├── lock/              # 文件锁定
│   │   ├── search/            # 搜索功能
│   │   ├── git/               # Git集成（GitPython）
│   │   └── mcp/               # MCP服务（SSE协议）
│   │       ├── server.py
│   │       ├── tools.py
│   │       └── auth.py        # MCP认证中间件
│   ├── tests/
│   └── pyproject.toml
├── frontend/                  # Vite + React前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── ThemeToggle.tsx     # 主题切换按钮
│   │   │   ├── Auth/              # 认证相关组件
│   │   │   ├── CodeEditor/        # 代码编辑器
│   │   │   ├── FileTree/          # 文件树（支持拖拽）
│   │   │   ├── GitHistory/        # Git历史查看
│   │   │   ├── MarkdownEditor/    # Markdown编辑
│   │   │   ├── MarkdownViewer/    # Markdown预览
│   │   │   └── Search/            # 搜索组件
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── KnowledgePage.tsx
│   │   │   ├── KnowledgePropertiesPage.tsx
│   │   │   └── AdminPage.tsx
│   │   ├── stores/
│   │   │   ├── authStore.ts       # 认证状态
│   │   │   ├── knowledgeStore.ts  # 知识库状态
│   │   │   └── themeStore.ts      # 主题状态
│   │   ├── lib/api.ts            # API客户端
│   │   └── types/                 # TypeScript类型
│   ├── Caddyfile              # Caddy配置（Docker部署）
│   └── tests/
├── data/                      # 知识库存储
│   └── knowledge/
├── .github/workflows/ci.yml  # GitHub Actions CI
├── docker-compose.yml
└── agents.md                  # 本文件
```

## 部署架构

### Docker + Caddy 部署

```
用户请求
    │
    ▼
┌─────────────────────────────────────┐
│  Caddy (端口可配置，默认80)          │
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

### 启动命令

```bash
# 默认端口 (80)
docker-compose up -d

# 自定义端口
APP_PORT=3000 docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## MCP 服务

### 概述

MCP (Model Context Protocol) 服务通过 SSE (Server-Sent Events) 协议提供，允许外部 AI Agent 访问知识库。

### 端点

- SSE 端点: `http://localhost/mcp/sse` (Docker) 或 `http://localhost:8000/mcp/sse` (开发)

### 提供的工具

| 工具名 | 说明 |
|--------|------|
| `list_knowledge_base` | 列出所有知识库 |
| `get_knowledge_detail` | 获取知识库详情 |
| `read_file_content` | 读取文件内容 |
| `update_file` | 更新文件内容 |
| `create_new_knowledge` | 创建新知识库 |
| `search_knowledge` | 搜索知识库 |
| `get_git_history` | 获取Git提交历史 |
| `get_file_diff` | 获取文件差异 |
| `commit_changes` | 提交更改 |

### 使用示例

```python
# 通过 MCP 客户端连接
from mcp import ClientSession, SSEServerTransport

transport = SSEServerTransport("http://localhost/mcp/sse")
async with ClientSession(transport) as session:
    # 列出知识库
    result = await session.call_tool("list_knowledge_base", {})
    print(result)
```

## 环境变量

### 后端

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/carrotcontext.db` | 数据库路径 |
| `JWT_SECRET_KEY` | `your-secret-key-change-in-production` | JWT 密钥 |
| `JWT_ALGORITHM` | `HS256` | JWT 算法 |
| `JWT_EXPIRE_MINUTES` | `30` | Token 过期时间 |
| `KNOWLEDGE_BASE_PATH` | `./data/knowledge` | 知识库存储路径 |
| `LOCK_TIMEOUT_MINUTES` | `30` | 文件锁超时 |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | CORS 允许来源 |
| `MCP_ENABLED` | `true` | 启用MCP服务 |
| `MCP_PATH` | `/mcp` | MCP挂载路径 |

### Docker

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_PORT` | `80` | 前端访问端口 |
| `JWT_SECRET_KEY` | `your-secret-key-change-in-production` | JWT 密钥 |

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
- 后端: pytest 覆盖率 > 80%
- 前端: Vitest 覆盖率 > 70%

### 前端视觉设计规范

采用现代 SaaS 科技风设计语言（参考 Notion/Linear 风格）：

- **色彩体系**: 主背景 `bg-slate-50`，文字 `text-slate-800`/`text-slate-900`，副文本 `text-slate-500`
- **圆角规范**: 卡片/按钮 `rounded-xl`，弹窗 `rounded-2xl`
- **阴影层次**: 基础 `shadow-sm`，悬浮 `hover:shadow-md`，弹窗 `shadow-xl shadow-slate-200/50`
- **边框**: 统一使用 `border-slate-100` 或 `border-slate-200/60`
- **按钮**: 主按钮使用渐变 `bg-gradient-to-r from-blue-600 to-indigo-600`
- **导航栏**: 毛玻璃效果 `bg-white/80 backdrop-blur-md`
- **输入框**: 聚焦光晕 `focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500`
- **图标**: 使用 lucide-react SVG 图标，文件类型用颜色区分
- **动效**: `transition-all duration-200`，悬浮上移 `hover:-translate-y-0.5`

## 核心模块说明

### 认证模块 (auth)
- JWT token认证（python-jose）
- 用户注册/登录
- 密码使用bcrypt哈希
- 管理员角色管理（用户列表、角色修改、删除用户）
- 首个注册用户自动成为管理员

### 知识管理 (knowledge)
- 文件系统存储，每个根节点有.manifest.json
- 支持文件/目录的CRUD操作
- 文件上传支持
- 知识库分类和标签系统
- 权限管理（admin/editor/viewer三级权限）

### 文件操作 (files)
- 文件读写、移动、上传
- 二进制文件下载（支持图片、PDF、压缩包等）
- 二进制文件检测（扩展名 + UTF-8解码验证）

### 文件锁定 (lock)
- 悲观锁实现，基于.lock文件
- 支持锁状态查询和超时处理

### 搜索 (search)
- 元数据搜索: SQLite LIKE查询
- 内容搜索: 优先使用 ripgrep，不可用时降级为 Python grep fallback

### Git集成 (git)
- 使用GitPython进行版本控制
- 支持提交历史、差异查看、版本回滚

### MCP服务 (mcp)
- SSE (Server-Sent Events) 协议
- 基于 FastMCP SDK
- 提供9个知识库访问工具
- 支持可选JWT认证（匿名用户使用默认权限）
- 通过Caddy反向代理访问

### 前端主题系统
- 支持浅色/深色/跟随系统三种模式
- 使用Zustand持久化到localStorage
- Tailwind CSS 4 `dark:` 原生支持
- Monaco编辑器主题自动切换

## API 端点

### 认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户
- `GET /api/auth/users` - 用户列表（管理员）
- `PUT /api/auth/users/{id}/role` - 修改用户角色（管理员）
- `DELETE /api/auth/users/{id}` - 删除用户（管理员）

### 知识库
- `GET /api/knowledge` - 列表
- `POST /api/knowledge` - 创建
- `GET /api/knowledge/{id}` - 详情
- `PUT /api/knowledge/{id}` - 更新
- `DELETE /api/knowledge/{id}` - 删除
- `GET /api/knowledge/{id}/tree` - 文件树
- `GET /api/knowledge/{id}/files/{path}` - 文件内容
- `PUT /api/knowledge/{id}/files/{path}` - 更新文件
- `POST /api/knowledge/{id}/files/move` - 移动文件
- `POST /api/knowledge/{id}/files/upload` - 上传文件
- `GET /api/knowledge/{id}/files/{path}/raw` - 下载二进制文件
- `POST /api/knowledge/{id}/dirs` - 创建目录
- `GET /api/knowledge/{id}/permissions` - 权限列表（管理员）
- `POST /api/knowledge/{id}/permissions` - 设置权限（管理员）
- `DELETE /api/knowledge/{id}/permissions/{perm_id}` - 删除权限（管理员）

### 搜索
- `GET /api/search?q={query}` - 搜索

### 文件锁定
- `POST /api/lock` - 获取锁
- `DELETE /api/lock` - 释放锁
- `GET /api/lock/status` - 锁状态

### Git
- `POST /api/git/{id}/init` - 初始化
- `GET /api/git/{id}/log` - 提交历史
- `GET /api/git/{id}/diff` - 差异
- `POST /api/git/{id}/commit` - 提交
- `POST /api/git/{id}/revert` - 回滚

### MCP
- `GET /mcp/sse` - MCP SSE 端点（支持可选JWT认证）

## 常用命令

```bash
# 后端
cd backend
uv sync                          # 安装依赖
uv run uvicorn app.main:app --reload  # 启动开发服务器
uv run pytest                    # 运行测试
uv run ruff check .              # 代码检查

# 前端
cd frontend
bun install                      # 安装依赖
bun dev                          # 启动开发服务器
bunx vitest run                  # 运行测试
bunx vite build                  # 构建生产版本

# Docker
docker-compose up -d             # 启动服务
docker-compose down              # 停止服务
docker-compose logs -f           # 查看日志
APP_PORT=3000 docker-compose up -d  # 自定义端口
```

## 注意事项

1. 知识库存储在data/knowledge/目录下，每个知识库是独立的文件夹
2. 每个知识库根目录有.manifest.json存储元数据
3. 文件锁定使用.lock文件，编辑前需要获取锁
4. Git版本控制为每个知识库独立初始化
5. MCP服务挂载在/mcp路径，SSE端点为/mcp/sse
6. 内容搜索优先使用ripgrep，如未安装会自动降级为Python grep
7. Docker部署使用Caddy作为反向代理，支持SPA路由和SSE流式传输
8. 端口可通过APP_PORT环境变量自定义
