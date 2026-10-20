"""支付台账 Schema"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════
# 创建支付记录（报送）
# ═══════════════════════════════════════════════════════════════════

class PaymentCreate(BaseModel):
    """录入报送金额"""
    stage_id: uuid.UUID = Field(..., description="关联支付节点ID")
    reported_amount: int = Field(..., ge=1, description="报送金额（分）")


# ═══════════════════════════════════════════════════════════════════
# 确认 / 驳回
# ═══════════════════════════════════════════════════════════════════

class PaymentConfirm(BaseModel):
    """确认批准（无字段，点按钮即确认）"""
    pass


class PaymentReject(BaseModel):
    """驳回"""
    reject_reason: str = Field(..., min_length=1, description="驳回原因")


# ═══════════════════════════════════════════════════════════════════
# 支付记录响应
# ═══════════════════════════════════════════════════════════════════

class PaymentResponse(BaseModel):
    """支付记录响应"""
    id: uuid.UUID
    contract_id: uuid.UUID
    contract_no: str
    stage_id: uuid.UUID | None = None
    reported_amount: int = 0
    approved_amount: int = 0
    status: str = "pending"
    reject_reason: str | None = None
    confirmed_at: datetime | None = None
    payment_voucher: str | None = None
    remark: str | None = None
    # ── 冗余字段（从关系取，方便前端展示） ──
    stage_name: str | None = None
    supplier_name: str | None = None
    # ── 时间戳 ──
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════
# 支付台账按月分组
# ═══════════════════════════════════════════════════════════════════

class PaymentLedgerGroup(BaseModel):
    """支付台账按月分组"""
    month: str = Field(..., description="月份，如 2026-01")
    items: list[PaymentResponse] = Field(default_factory=list, description="当月支付记录")
    month_total_reported: int = Field(0, description="当月报送总额（分）")
    month_total_approved: int = Field(0, description="当月批准总额（分）")
