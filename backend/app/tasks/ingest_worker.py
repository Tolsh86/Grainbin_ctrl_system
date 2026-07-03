"""清洗流水线 Celery 异步任务

接收 batch_id，执行 5 步清洗流水线：
    Parse → Normalize → Map → Validate → 暂存
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.tasks.celery_app import celery_app

# 在 worker 进程中创建独立的异步引擎
engine = create_async_engine(settings.DATABASE_URL)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@celery_app.task(bind=True, name="process_ingest_batch")
def process_ingest_batch(self, batch_id: str):
    """清洗批次主任务。

    状态流转：pending → parsing → normalized → validated → review
    """
    return _run_async(_process_batch(str(batch_id)))


async def _process_batch(batch_id: str) -> str:
    """异步清洗流水线核心逻辑（骨架）。"""
    from app.models.ingest import IngestBatch

    async with async_session() as db:
        result = await db.execute(select(IngestBatch).where(IngestBatch.id == uuid.UUID(batch_id)))
        batch = result.scalar_one_or_none()
        if not batch:
            return f"批次 {batch_id} 不存在"

        try:
            # Step 1: 解析（parse）
            batch.status = "parsing"
            await db.commit()
            # TODO: 根据 file_format 选择解析器
            #   - xlsx/xls: OpenPyXL 解析
            #   - csv: pandas 解析
            #   - pdf: pdfplumber + PaddleOCR
            #   - image: PaddleOCR
            #   解析结果写入 IngestRow(raw_payload)

            # Step 2: 归一化（normalize）
            batch.status = "normalized"
            await db.commit()
            # TODO: 对每行应用 converter 链
            #   金额: yuan_to_fen / wan_yuan_to_fen
            #   日期: chinese_date_to_iso / excel_serial_to_date / iso_date
            #   字符串: trim / lowercase / normalize_whitespace
            #   别名: category_alias_to_canonical
            #   单位: decimal_to_base_unit
            #   结果写入 IngestRow.normalized

            # Step 3: 字段映射（map）
            # TODO: 按 t_field_mappings.rules 做字段映射
            #   结果写入 IngestRow.mapped

            # Step 4: 校验（validate）
            batch.status = "validated"
            await db.commit()
            # TODO: 运行 5 类校验
            #   必填 / 类型 / 范围 / 引用 / 唯一
            #   错误行 → IngestError + is_valid=False
            #   通过行 → is_valid=True
            #   更新 batch.error_rows / batch.valid_rows

            # Step 5: 进入暂存（review）
            batch.status = "review"
            batch.quality_score = _calc_quality_score(batch)
            await db.commit()

            return f"批次 {batch_id} 处理完成: total={batch.total_rows}, valid={batch.valid_rows}, errors={batch.error_rows}"

        except Exception as exc:
            batch.status = "failed"
            await db.commit()
            return f"批次 {batch_id} 处理失败: {exc}"


def _calc_quality_score(batch: object) -> float:
    """计算批次质量分: 100 - (error_rows / total_rows) × 100。"""
    batch.total_rows = getattr(batch, "total_rows", 0)
    batch.error_rows = getattr(batch, "error_rows", 0)
    if batch.total_rows == 0:
        return 0.0
    return max(0.0, 100.0 - (batch.error_rows / batch.total_rows) * 100)


def _run_async(coro):
    """在同步任务函数中运行异步协程。"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
