"""pytest 配置：测试用异步数据库引擎与会话"""

from __future__ import annotations

import datetime

import pytest
import pytest_asyncio
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# ── 测试用 ORM 基类 ──────────────────────────────────


class TestBase(DeclarativeBase):
    pass


class TestModel(TestBase):
    """测试用模型 — 有 deleted_at 的软删除模型"""

    __test__ = False
    __tablename__ = "test_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True, default=None)


class NoSoftDeleteModel(TestBase):
    """测试用模型 — 没有 deleted_at"""

    __test__ = False
    __tablename__ = "test_no_soft_delete"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


# ── pytest-asyncio fixture ───────────────────────────


@pytest_asyncio.fixture
async def db_session():
    """提供测试用异步数据库会话（内存 SQLite）。

    每次测试自动建表并填充测试数据。
    """
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 插入软删除模型数据
        session.add_all([
            TestModel(name="normal_1", status="active"),
            TestModel(name="normal_2", status="active"),
            TestModel(name="normal_3", status="active"),
            TestModel(name="deleted_1", status="active", deleted_at=func.now()),
            TestModel(name="deleted_2", status="inactive", deleted_at=func.now()),
            TestModel(name="inactive_1", status="inactive"),
            TestModel(name="inactive_2", status="inactive"),
            TestModel(name="normal_4", status="active"),
        ])
        # 插入非软删除模型数据
        session.add_all([
            NoSoftDeleteModel(name="item_1", status="active"),
            NoSoftDeleteModel(name="item_2", status="active"),
        ])
        await session.flush()
        yield session

    await engine.dispose()
