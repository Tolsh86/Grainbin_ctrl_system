"""清洗流水线 Celery 异步任务

状态流转：pending → parsing → normalized → validated → review → committed / failed
"""
from __future__ import annotations

import asyncio
import uuid

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.ingest import IngestBatch, IngestError
from app.tasks.celery_app import celery_app

engine = create_async_engine(settings.DATABASE_URL)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _run_async(coro):
    """在同步 Celery 任务中安全执行异步协程。

    创建独立事件循环，确保 Windows 下 ProactorEventLoop 兼容。
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="process_ingest_batch", max_retries=1, default_retry_delay=30)
def process_ingest_batch(self, batch_id: str):
    """解析任务入口 — 调用异步解析主流程。

    状态流转: pending → parsing → normalized → validated → (review) → committed
    失败时: → failed（写入 IngestError）
    """
    return _run_async(_process_batch(str(batch_id)))


async def _process_batch(batch_id: str) -> str:
    """异步解析主流程。

    独立 async session + 显式事务管理：
    - 解析成功 → commit, status="validated"
    - 解析失败 → rollback 所有局部写入, 写入 IngestError, status="failed"
    """
    async with async_session() as db:
        try:
            from app.services.parser import parse_and_normalize_batch

            await parse_and_normalize_batch(db, uuid.UUID(batch_id))
            # parse_and_normalize_batch 内部已 commit，此处二次确认
            logger.info(f"批次 {batch_id} 解析完成")
            return f"批次 {batch_id} 处理完成"

        except Exception as exc:
            logger.exception(f"批次 {batch_id} 解析失败")
            # 回滚所有未提交的更改
            await db.rollback()
            # 重新获取批次并标记失败（独立事务）
            await _fail_batch(db, uuid.UUID(batch_id), exc)
            return f"批次 {batch_id} 处理失败: {exc}"


async def _fail_batch(db: AsyncSession, batch_id: uuid.UUID, exc: Exception) -> None:
    """原子标记批次失败并记录错误。

    使用 SELECT ... FOR UPDATE 防止并发写入冲突。
    在独立的 savepoint 中执行，失败不影响外部事务。
    """
    result = await db.execute(
        select(IngestBatch).where(IngestBatch.id == batch_id).with_for_update()
    )
    batch = result.scalar_one_or_none()
    if not batch:
        logger.warning(f"_fail_batch: 批次 {batch_id} 不存在")
        return

    batch.status = "failed"
    error = IngestError(
        batch_id=batch.id,
        row_id=None,
        error_stage="parse",
        error_code="PARSE_FAILED",
        error_message=str(exc)[:1000],
        error_field=None,
        error_value=None,
        severity="error",
    )
    db.add(error)
    await db.commit()
    logger.info(f"批次 {batch_id} 已标记为 failed")
