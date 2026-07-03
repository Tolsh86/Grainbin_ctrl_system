# 生产环境部署指南

## 概述

生产环境采用单机 Docker Compose 部署方案（或 2 台应用 + 1 台 DB）。

## 前置要求

- Docker 24+
- Docker Compose v2
- 至少 4 核 CPU / 16 GB 内存 / 100 GB 磁盘

## 部署步骤

### 1. 克隆代码并配置环境变量

```bash
git clone <repo-url>
cd Grainbin_system

# 复制并编辑环境变量
cp docker/.env.docker docker/.env
vi docker/.env  # 修改密码等敏感信息
cp backend/.env.example backend/.env
vi backend/.env
```

### 2. 启动服务

```bash
# 启动基础设施
cd docker && docker compose up -d

# 初始化数据库
cd ../backend
poetry install --no-dev
poetry run alembic upgrade head

# 启动应用（生产模式）
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. 前端部署

```bash
cd frontend
npm ci
npm run build
# 将 dist/ 目录部署到 Nginx
```

### 4. Nginx 反向代理（推荐）

将 Nginx 配置为反向代理，统一入口。
SSL 证书推荐使用 Let's Encrypt。

### 5. 备份

- PostgreSQL: `pg_dump` 定时备份
- MinIO: `mc mirror` 定时同步到备机
- 建议设置 crontab 每日自动备份
