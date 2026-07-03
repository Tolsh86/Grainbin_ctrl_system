# 粮仓项目全过程控制（过控）智能管理系统

## 技术栈

- **后端**: Python FastAPI + SQLAlchemy 2.0 异步 + Alembic
- **前端**: React 18 + Vite + Ant Design 5
- **数据库**: PostgreSQL 15 + pgvector
- **缓存/队列**: Redis 7.x
- **对象存储**: MinIO
- **任务队列**: Celery + Redis
- **日志**: Loguru
- **依赖管理**: uv (后端) / npm (前端)

## 前置条件

1. 安装 [uv](https://docs.astral.sh/uv/getting-started/installation/) (推荐全局安装，比 pip 快 10-100 倍)

   ```bash
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

   # macOS / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
3. 安装 [Node.js](https://nodejs.org/) (推荐 >= 18 LTS)

## 一键启动

```bash
# 1. 启动基础设施（PostgreSQL + Redis + MinIO）
cd docker
docker compose up -d

# 2. 启动后端（自动创建虚拟环境、安装依赖、启动服务）
cd ../backend
uv sync                     # 自动创建 .venv 并安装所有依赖
cp -n .env.example .env 2>/dev/null; true  # 首次需编辑 .env
uv run alembic upgrade head # 数据库初始化
uv run uvicorn app.main:app --reload

# 3. 启动前端（新终端）
cd ../frontend
npm install
npm run dev
```

## 快速启动（分步说明）

### 1. 启动基础设施

```bash
cd docker
docker compose up -d
```

启动 PostgreSQL (含 pgvector)、Redis、MinIO、PgAdmin。

### 2. 初始化后端

```bash
cd backend

# 同步依赖（等价于 poetry install，uv 自动管理虚拟环境）
uv sync

# 安装开发依赖也一起
# uv sync（默认安装含 dev 的所有 group）

# 配置环境变量
cp .env.example .env  # 编辑 .env 修改数据库连接等配置

# 数据库迁移
uv run alembic upgrade head

# 启动开发服务器
uv run uvicorn app.main:app --reload
```

访问 http://localhost:8000/docs 查看 API 文档。

#### uv 常用命令速查

| 命令 | 说明 |
|------|------|
| `uv sync` | 安装/同步所有依赖（生产 + 开发） |
| `uv sync --no-dev` | 仅安装生产依赖 |
| `uv add <pkg>` | 添加一个新依赖 |
| `uv add --dev <pkg>` | 添加开发依赖 |
| `uv remove <pkg>` | 移除依赖 |
| `uv run <command>` | 在虚拟环境中运行命令 |
| `uv lock --upgrade` | 更新所有依赖锁文件 |
| `uv python list` | 查看可用 Python 版本 |
| `uv python pin 3.11` | 固定 Python 版本 |

### 3. 初始化前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 打开应用。

### 4. 数据库迁移

后续数据模型变更只需修改 models 定义，然后运行：

```bash
cd backend
uv run alembic revision --autogenerate -m "描述你的变更"
uv run alembic upgrade head
```

## 项目结构

```
Grainbin_system/
├── docker/          # Docker Compose 基础设施
├── backend/         # FastAPI 后端
│   ├── app/
│   │   ├── core/    # 配置、数据库、安全
│   │   ├── models/  # ORM 模型（16张表）
│   │   ├── schemas/ # Pydantic 请求/响应
│   │   ├── routers/ # API 路由
│   │   ├── services/# 业务逻辑
│   │   ├── utils/   # 工具模块
│   │   └── tasks/   # Celery 异步任务
│   ├── alembic/     # 数据库迁移
│   ├── pyproject.toml  # 项目元数据与依赖
│   ├── uv.lock         # uv 锁文件（相当于 poetry.lock）
│   └── .python-version # Python 版本固定
├── frontend/        # React 前端
└── deploy/          # 部署配置
```
