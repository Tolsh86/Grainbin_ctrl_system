"""Alembic 异步环境配置

支持 autogenerate 自动检测 ORM 模型变更。
"""

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# 将 backend 目录加入 Python 路径
# 将 backend 目录加入 Python 路径，确保 `from app.models import Base` 可用
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings
from app.models import Base  # noqa: E402, F401 — 导入所有模型

# Alembic Config 对象
config = context.config

# 用 settings.DATABASE_URL 覆盖 alembic.ini 中的 sqlalchemy.url
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+asyncpg", ""))

# 设置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData 用于 autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线迁移模式 — 生成 SQL 脚本而非直接执行。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """在异步连接上下文中运行迁移。"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """在线异步迁移模式。"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线迁移模式入口。"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
