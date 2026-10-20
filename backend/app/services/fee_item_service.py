"""费用分项业务逻辑 (Phase2)

t_contract_fee_items — 合同费用分项定义（模板）CRUD
t_review_fee_items — 审核费用分项值（快照）更新
"""

from __future__ import annotations

import uuid

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contract_fee_item import ContractFeeItem
from app.models.review_fee_item import ReviewFeeItem
from app.core.exceptions import NotFound, BadRequest


# ═══════════════════════════════════════════════════════════════════
# 合同费用分项定义（模板）CRUD
# ═══════════════════════════════════════════════════════════════════

async def get_contract_fee_items(
    db: AsyncSession, contract_id: uuid.UUID
) -> list[ContractFeeItem]:
    """获取合同的所有费用分项模板。"""
    result = await db.execute(
        select(ContractFeeItem)
        .where(ContractFeeItem.contract_id == contract_id)
        .order_by(ContractFeeItem.sort_order)
    )
    return list(result.scalars().all())


async def get_contract_fee_item(
    db: AsyncSession, fee_item_id: uuid.UUID
) -> ContractFeeItem | None:
    """获取单个费用分项模板。"""
    return await db.get(ContractFeeItem, fee_item_id)


async def create_contract_fee_items(
    db: AsyncSession,
    contract_id: uuid.UUID,
    items: list[dict],
) -> list[ContractFeeItem]:
    """批量创建合同费用分项模板。"""
    created = []
    for item_data in items:
        fee_item = ContractFeeItem(
            contract_id=contract_id,
            item_name=item_data["item_name"],
            contract_amount=item_data.get("contract_amount"),
            current_ratio=item_data.get("current_ratio"),
            sort_order=item_data.get("sort_order", len(created)),
            remark=item_data.get("remark"),
        )
        db.add(fee_item)
        created.append(fee_item)

    await db.flush()
    logger.info(f"费用分项模板创建: contract={contract_id}, count={len(created)}")
    return created


async def update_contract_fee_item(
    db: AsyncSession,
    fee_item_id: uuid.UUID,
    data: dict,
) -> ContractFeeItem | None:
    """更新单个费用分项模板。"""
    fee_item = await db.get(ContractFeeItem, fee_item_id)
    if not fee_item:
        return None

    for key, value in data.items():
        if value is not None:
            setattr(fee_item, key, value)

    await db.flush()
    await db.refresh(fee_item)
    return fee_item


async def delete_contract_fee_item(
    db: AsyncSession, fee_item_id: uuid.UUID
) -> bool:
    """删除费用分项模板。已关联的审核快照 fee_item_id 会 ON DELETE SET NULL。"""
    fee_item = await db.get(ContractFeeItem, fee_item_id)
    if not fee_item:
        return False
    await db.delete(fee_item)
    await db.flush()
    return True


# ═══════════════════════════════════════════════════════════════════
# 审核费用分项值（快照）更新
# ═══════════════════════════════════════════════════════════════════

async def update_review_fee_item(
    db: AsyncSession,
    fee_item_id: uuid.UUID,
    reviewed_amount: int | None = None,
    remark: str | None = None,
) -> ReviewFeeItem | None:
    """更新审核费用分项值（报送值只读，审定值可编辑）。"""
    item = await db.get(ReviewFeeItem, fee_item_id)
    if not item:
        return None

    if reviewed_amount is not None:
        if reviewed_amount < 0:
            raise BadRequest(detail="审定金额不能为负数")
        item.reviewed_amount = reviewed_amount
    if remark is not None:
        item.remark = remark

    await db.flush()
    await db.refresh(item)
    return item


async def get_review_fee_items(
    db: AsyncSession, review_id: uuid.UUID
) -> list[ReviewFeeItem]:
    """获取审核记录下的所有费用分项。"""
    result = await db.execute(
        select(ReviewFeeItem)
        .where(ReviewFeeItem.review_id == review_id)
        .order_by(ReviewFeeItem.item_name)
    )
    return list(result.scalars().all())
