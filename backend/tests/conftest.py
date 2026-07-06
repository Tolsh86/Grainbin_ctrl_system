"""pytest 配置：SQLite 测试数据库 + FastAPI TestClient + Mock 外部依赖

提供：
- SQLite 内存数据库，自动建表（自动处理 PG → SQLite 类型适配）
- httpx AsyncClient（模拟 FastAPI 请求）
- 预设用户 (admin, operator, viewer) + 认证 Token 辅助函数
- Mock MinIO + Celery（避免需要外部服务）
"""

from __future__ import annotations

import datetime
import uuid
from collections.abc import AsyncGenerator, AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

# ── PG → SQLite 类型适配 ─────────────────────────────
# 必须在模型导入前注册，否则 create_all 会失败

import json
from datetime import date, datetime

from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID, TSVECTOR
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

# UUID: PG UUID → SQLite CHAR(36)
@compiles(PG_UUID, "sqlite")
def _compile_pg_uuid_sqlite(type_, compiler, **kw):
    return "CHAR(36)"

# 自定义 JSON 序列化器：支持 date/datetime
def _json_date_serializer(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# JSONB → SQLite JSON（SQLite 3.38+ 原生支持）
@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return compiler.visit_JSON(type_, **kw)

# TSVECTOR → SQLite TEXT（全文搜索在测试中不需要）
@compiles(TSVECTOR, "sqlite")
def _compile_tsvector_sqlite(type_, compiler, **kw):
    return "TEXT"


# ── Mock 外部依赖 ────────────────────────────────────

from unittest.mock import AsyncMock, MagicMock, patch

_mock_minio = MagicMock()
_mock_minio.upload_bytes = MagicMock(return_value="mock/path/file.xlsx")
_mock_redis = MagicMock()
_mock_celery = MagicMock()

with patch("app.utils.minio_client.MinioClient", return_value=_mock_minio):
    with patch("app.utils.redis_client.RedisClient", return_value=_mock_redis):
        with patch("app.tasks.celery_app.celery_app", _mock_celery):
            from app.main import app as fastapi_app

# 直接 Mock 全局 minio_client 单例的方法，确保上传回路不调用真实 MinIO
from app.utils.minio_client import minio_client as _real_minio_client
_real_minio_client.upload_bytes = MagicMock(return_value="mock/path/file.xlsx")


# ── 数据库引擎 ──────────────────────────────────────


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """为每个测试函数创建独立的 SQLite 内存数据库。"""
    from app.models.base import Base

    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    # 启用 SQLite 外键约束
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    # 修复 SQLite JSON 序列化：支持 date/datetime 对象
    engine.sync_engine.dialect._json_serializer = lambda obj: json.dumps(obj, default=_json_date_serializer)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncIterator[AsyncSession]:
    """创建独立事务的数据库会话，测试结束自动回滚。"""
    conn = await test_engine.connect()
    trans = await conn.begin()

    session_factory = async_sessionmaker(
        bind=conn, class_=AsyncSession, expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    async with session_factory() as session:
        yield session

    await trans.rollback()
    await conn.close()


# ── FastAPI TestClient ──────────────────────────────


@pytest_asyncio.fixture(scope="function")
async def client(test_engine, db_session) -> AsyncIterator[AsyncClient]:
    """通过依赖注入替换 get_db，Mock MinIO/Celery，返回 httpx AsyncClient。"""
    from app.core.database import get_db

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _override_get_db

    # Celery mock（避免需要 Redis broker）
    _mock_celery.send_task = MagicMock()

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    fastapi_app.dependency_overrides.clear()


# ── Auth 辅助 ────────────────────────────────────────


def _make_auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def register_and_login(
    client: AsyncClient,
    username: str,
    password: str,
    real_name: str,
    role: str = "operator",
) -> tuple[uuid.UUID, str]:
    """在测试中注册用户并登录，返回 (user_id, access_token)。"""
    resp = await client.post("/api/v1/auth/register", json={
        "username": username,
        "password": password,
        "real_name": real_name,
        "role": role,
    })
    assert resp.status_code == 201, f"注册失败: {resp.json()}"
    user_id = uuid.UUID(resp.json()["id"])

    # 注册返回的响应不含 token，手动签发一个
    from app.core.security import create_access_token

    token = create_access_token(data={"sub": str(user_id)})
    return user_id, token


# ── 预设用户 fixtures ────────────────────────────────


@pytest_asyncio.fixture(scope="function")
async def admin_auth(client) -> tuple[uuid.UUID, str]:
    """管理员用户（已注册+登录）。"""
    return await register_and_login(client, "admin", "admin123", "管理员", role="admin")


@pytest_asyncio.fixture(scope="function")
async def operator_auth(client) -> tuple[uuid.UUID, str]:
    """操作员用户（已注册+登录）。"""
    return await register_and_login(client, "operator", "oper123", "操作员", role="operator")


@pytest_asyncio.fixture(scope="function")
async def viewer_auth(client) -> tuple[uuid.UUID, str]:
    """查看者用户（已注册+登录）。"""
    return await register_and_login(client, "viewer", "view123", "查看者", role="viewer")


# ── 预置项目 fixture ──────────────────────────────────


@pytest_asyncio.fixture(scope="function")
async def test_project(client, operator_auth) -> uuid.UUID:
    """创建一个测试用项目，返回 project_id。"""
    _uid, token = operator_auth
    resp = await client.post("/api/v1/projects", json={
        "project_name": "测试粮仓工程",
        "project_code": "TEST-2026-001",
        "project_nature": "功能性项目",
        "invest_timing": "新投项目",
        "region": "市内",
        "planned_total_invest": 100000000,
        "project_status": "constructing",
    }, headers=_make_auth_header(token))
    assert resp.status_code == 201, f"创建项目失败: {resp.json()}"
    return uuid.UUID(resp.json()["id"])


# ── 测试用 Excel 文件生成器 ──────────────────────────


@pytest.fixture(scope="function")
def sample_excel_bytes() -> bytes:
    """在内存中生成一个简单 xlsx 文件，含表头和数据行。"""
    import io

    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["序号", "日期", "分项名称", "计划量", "实际量", "单位", "单价(元)", "金额(元)"])
    ws.append([1, "2026-07-01", "桩基础", 100, 85, "根", 5000, 425000])
    ws.append([2, "2026-07-01", "土方开挖", 5000, 4800, "m³", 30, 144000])
    ws.append([3, "2026-07-01", "钢筋绑扎", 200, 160, "吨", 4500, 720000])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
