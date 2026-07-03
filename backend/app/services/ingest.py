"""清洗流水线业务逻辑"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingest import IngestBatch, IngestRow, IngestError, FieldMapping
from app.models.data_row import DataRow


async def create_batch(
    db: AsyncSession,
    project_id: uuid.UUID,
    source_doc: str,
    source_path: str,
    file_format: str,
    uploaded_by: uuid.UUID,
    mapping_id: uuid.UUID | None = None,
) -> IngestBatch:
    """创建清洗批次（status=pending）。"""
    batch = IngestBatch(
        project_id=project_id,
        source_doc=source_doc,
        source_path=source_path,
        source_type="upload",
        file_format=file_format,
        mapping_id=mapping_id,
        uploaded_by=uploaded_by,
        status="pending",
    )
    db.add(batch)
    await db.flush()
    await db.refresh(batch)
    return batch


async def get_batches(
    db: AsyncSession,
    project_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[IngestBatch], int]:
    """分页查询批次列表。"""
    query = select(IngestBatch)
    count_query = select(func.count(IngestBatch.id))

    if project_id:
        query = query.where(IngestBatch.project_id == project_id)
        count_query = count_query.where(IngestBatch.project_id == project_id)

    total = (await db.execute(count_query)).scalar_one()
    items = (
        await db.execute(
            query.order_by(IngestBatch.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    return list(items), total


async def get_batch(db: AsyncSession, batch_id: uuid.UUID) -> IngestBatch | None:
    result = await db.execute(select(IngestBatch).where(IngestBatch.id == batch_id))
    return result.scalar_one_or_none()


async def get_batch_rows(
    db: AsyncSession,
    batch_id: uuid.UUID,
    is_valid: bool | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[IngestRow], int]:
    """查询批次中的清洗行，可按 is_valid 筛选。"""
    query = select(IngestRow).where(IngestRow.batch_id == batch_id)
    count_query = select(func.count(IngestRow.id)).where(IngestRow.batch_id == batch_id)

    if is_valid is not None:
        query = query.where(IngestRow.is_valid == is_valid)
        count_query = count_query.where(IngestRow.is_valid == is_valid)

    total = (await db.execute(count_query)).scalar_one()
    items = (
        await db.execute(
            query.order_by(IngestRow.row_no)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    return list(items), total


async def commit_batch(db: AsyncSession, batch_id: uuid.UUID) -> IngestBatch | None:
    """确认入库：将批次中 is_valid=True 的行写入 t_data_rows。"""
    batch = await get_batch(db, batch_id)
    if not batch or batch.status not in ("review", "validated"):
        return None

    # 获取所有校验通过的行
    result = await db.execute(
        select(IngestRow).where(IngestRow.batch_id == batch_id, IngestRow.is_valid == True)
    )
    valid_rows = result.scalars().all()

    for row in valid_rows:
        data_row = DataRow(
            project_id=row.project_id,
            data_date=row.data_date,
            category=row.category,
            item_name=row.item_name,
            planned_quantity=row.planned_quantity,
            actual_quantity=row.actual_quantity,
            unit=row.unit,
            unit_price=row.unit_price,
            amount=row.amount,
            cost_type=row.cost_type,
            source_doc=batch.source_doc,
            source_type="upload",
            is_confirmed=True,
            confirmed_at=datetime.now(UTC),
        )
        db.add(data_row)
        await db.flush()
        row.target_data_row_id = data_row.id

    batch.status = "committed"
    batch.committed_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(batch)
    return batch


async def rollback_batch(db: AsyncSession, batch_id: uuid.UUID) -> IngestBatch | None:
    """整批撤回：将已入库的 t_data_rows 软删除。"""
    batch = await get_batch(db, batch_id)
    if not batch or batch.status != "committed":
        return None

    # 查找已映射的 data_row
    result = await db.execute(
        select(IngestRow).where(
            IngestRow.batch_id == batch_id,
            IngestRow.target_data_row_id.isnot(None),
        )
    )
    rows = result.scalars().all()

    for row in rows:
        if row.target_data_row_id:
            data_result = await db.execute(
                select(DataRow).where(DataRow.id == row.target_data_row_id)
            )
            data_row = data_result.scalar_one_or_none()
            if data_row:
                data_row.deleted_at = datetime.now(UTC)

    batch.status = "rolled_back"
    batch.rolled_back_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(batch)
    return batch
