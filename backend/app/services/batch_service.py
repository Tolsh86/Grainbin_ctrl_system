"""导入批次状态管理服务"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, NotFound
from app.models.ingest import IngestBatch, IngestError
from app.tasks.celery_app import celery_app


ALLOWED_TRIGGER_STATUSES = {"pending", "failed"}


async def get_batch(db: AsyncSession, batch_id: uuid.UUID) -> IngestBatch:
    """获取批次详情，不存在则抛 404。"""
    result = await db.execute(select(IngestBatch).where(IngestBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise NotFound(detail="批次不存在")
    return batch


async def parse_batch(db: AsyncSession, batch_id: uuid.UUID) -> IngestBatch:
    """触发异步解析任务。

    状态校验 → 标记 parsing → 分发 Celery 任务。
    事务内原子更新状态，避免并发重入。
    """
    batch = await get_batch(db, batch_id)
    if batch.status not in ALLOWED_TRIGGER_STATUSES:
        raise BadRequest(
            detail=f"当前状态不允许解析: {batch.status}（仅 {', '.join(ALLOWED_TRIGGER_STATUSES)} 可触发）",
        )

    batch.status = "parsing"
    await db.flush()
    batch_id_str = str(batch.id)

    # 异步分发 Celery 任务（不阻塞请求）
    celery_app.send_task("process_ingest_batch", args=[batch_id_str])

    return batch


async def get_batch_rows(
    db: AsyncSession,
    batch: IngestBatch,
    page: int,
    page_size: int,
    is_valid: bool | None = None,
) -> tuple[list, int]:
    """分页查询批次中的清洗行。"""
    from sqlalchemy import func

    from app.models.ingest import IngestRow

    query = select(IngestRow).where(IngestRow.batch_id == batch.id)
    count_q = select(func.count(IngestRow.id)).where(IngestRow.batch_id == batch.id)

    if is_valid is not None:
        query = query.where(IngestRow.is_valid == is_valid)
        count_q = count_q.where(IngestRow.is_valid == is_valid)

    total = (await db.execute(count_q)).scalar_one()
    items = (
        await db.execute(
            query.order_by(IngestRow.row_no)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    return list(items), total


async def get_batch_errors(
    db: AsyncSession,
    batch_id: uuid.UUID,
    page: int,
    page_size: int,
    severity: str | None = None,
) -> tuple[list, int]:
    """分页查询批次错误记录。"""
    from sqlalchemy import func

    query = select(IngestError).where(IngestError.batch_id == batch_id).order_by(IngestError.created_at.desc())
    count_q = select(func.count(IngestError.id)).where(IngestError.batch_id == batch_id)

    if severity:
        query = query.where(IngestError.severity == severity)
        count_q = count_q.where(IngestError.severity == severity)

    total = (await db.execute(count_q)).scalar_one()
    items = (
        await db.execute(
            query.offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()

    return list(items), total
