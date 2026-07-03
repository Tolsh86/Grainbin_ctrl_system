"""
粮仓项目全过程控制（过控）智能管理系统 — FastAPI 入口

启动方式:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.routers.api import api_router


# ── 日志配置 ──────────────────────────────────────
logger.remove()
logger.add(
    sys.stderr,
    level="DEBUG" if settings.DEBUG else "INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)
logger.add(
    "logs/grainbin_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)


# ── 应用生命周期 ──────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭事件。"""
    logger.info(f"🚀 {settings.APP_NAME} 启动中...")

    # Redis
    try:
        from app.utils.redis_client import redis_client
        await redis_client.init()
        logger.info("✅ Redis 连接正常")
    except Exception as e:
        logger.warning(f"⚠️ Redis 连接失败: {e}")

    # MinIO
    try:
        from app.utils.minio_client import minio_client
        await minio_client.init()
        logger.info("✅ MinIO 连接正常")
    except Exception as e:
        logger.warning(f"⚠️ MinIO 连接失败: {e}")

    # 验证数据库连接
    try:
        from app.core.database import engine
        async with engine.connect() as conn:
            await conn.exec_driver_sql("SELECT 1")
        logger.info("✅ 数据库连接正常")
    except Exception as e:
        logger.warning(f"⚠️ 数据库连接失败: {e}")

    yield

    # 关闭资源
    try:
        from app.utils.redis_client import redis_client
        await redis_client.close()
    except Exception:
        pass
    logger.info(f"👋 {settings.APP_NAME} 已关闭")


# ── FastAPI 实例 ──────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="专为粮仓类工程全过程控制（过控）场景设计的智能管理系统",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# ── CORS 中间件 ───────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 路由 ──────────────────────────────────────────
app.include_router(api_router)

# ── 异常处理器 ──────────────────────────────────────
register_exception_handlers(app)


# ── 健康检查 ──────────────────────────────────────
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查端点。"""
    return {"status": "ok", "app": settings.APP_NAME, "version": "0.1.0"}
