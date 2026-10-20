"""支付台账路由

路由设计（V2.2 重构）：
所有支付操作挂载在合同下，以 contract_id 为路径参数。
- GET    ""                              → 查某合同支付台账（按月分组）
- POST   ""                              → 录入报送金额（系统自动算批准金额）
- POST   "/{payment_id}/confirm"         → 确认批准
- POST   "/{payment_id}/reject"          → 驳回

无 DELETE（驳回替代删除），无 PUT（驳回后重新 POST 一笔新的即可）。
"""

from __future__ import annotations

import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.payment import (
    PaymentCreate,
    PaymentReject,
    PaymentResponse,
    PaymentLedgerGroup,
)
from app.services import contract as contract_service
from app.services.contract import _payment_to_response

router = APIRouter(prefix="/contracts/{contract_id}/payments", tags=["支付台账"])


@router.get(
    "",
    response_model=list[PaymentLedgerGroup],
)
async def get_contract_payments(
    contract_id: uuid.UUID,
    year: int | None = Query(None, description="筛选年份，如 2026"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取合同支付台账，按 confirmed_at 月份分组。

    未确认（pending / rejected）的记录归入"未确认"分组。
    可选 year 参数筛选确认年份。
    """
    payments = await contract_service.get_contract_payments(db, contract_id, year=year)

    # ── 按月份分组 ──
    groups_map: dict[str, list] = defaultdict(list)
    for p in payments:
        if p.confirmed_at:
            month_key = p.confirmed_at.strftime("%Y-%m")
        else:
            month_key = "未确认"
        groups_map[month_key].append(p)

    groups: list[PaymentLedgerGroup] = []
    # "未确认"分组始终放在最前面
    if "未确认" in groups_map:
        items = groups_map.pop("未确认")
        groups.append(PaymentLedgerGroup(
            month="未确认",
            items=[_payment_to_response(p) for p in items],
            month_total_reported=sum(p.reported_amount for p in items),
            month_total_approved=sum(p.approved_amount for p in items),
        ))

    for month in sorted(groups_map.keys(), reverse=True):
        items = groups_map[month]
        groups.append(PaymentLedgerGroup(
            month=month,
            items=[_payment_to_response(p) for p in items],
            month_total_reported=sum(p.reported_amount for p in items),
            month_total_approved=sum(p.approved_amount for p in items),
        ))

    return groups


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    contract_id: uuid.UUID,
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """报送支付记录（需 operator 及以上权限）。

    系统自动计算批准金额（不超节点剩余额度）。
    """
    payment = await contract_service.create_payment(db, contract_id, data)
    return _payment_to_response(payment)


@router.post(
    "/{payment_id}/confirm",
    response_model=PaymentResponse,
)
async def confirm_payment(
    contract_id: uuid.UUID,
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """确认批准支付（需 operator 及以上权限）。

    只有 pending 状态的支付记录可以确认。
    """
    payment = await contract_service.confirm_payment(db, payment_id)
    return _payment_to_response(payment)


@router.post(
    "/{payment_id}/reject",
    response_model=PaymentResponse,
)
async def reject_payment(
    contract_id: uuid.UUID,
    payment_id: uuid.UUID,
    data: PaymentReject,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """驳回支付（需 operator 及以上权限）。

    必须填写驳回原因。
    只有 pending 状态的支付记录可以驳回。
    """
    payment = await contract_service.reject_payment(db, payment_id, data.reject_reason)
    return _payment_to_response(payment)
