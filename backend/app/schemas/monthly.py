"""月度台账 Schema：请求/响应模型"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════
# 台账列表
# ═══════════════════════════════════════════════════════════════════

class MonthlyFeeItem(BaseModel):
    """月度台账 — 单个分项"""
    fee_item_id: str = ""
    name: str = ""
    output: int = 0
    payable: int = 0


class MonthlyContractItem(BaseModel):
    """月度台账 — 单个合同行"""
    detail_id: uuid.UUID | None = None
    contract_id: uuid.UUID
    contract_no: str
    supplier_name: str = ""
    review_mode: str | None = None
    ledger_group: str | None = None
    contract_group: str | None = None
    contract_amount: int | None = None
    monthly_output: int = 0
    monthly_payable: int = 0
    cumulative_output: int = 0
    cumulative_payable: int = 0
    completed_ratio: float | None = None
    fee_items: list[MonthlyFeeItem] = Field(default_factory=list)
    source: str = "auto"
    status: str = "pending"


class MonthlyListGroup(BaseModel):
    """月度台账 — 按月份分组"""
    month: str
    contracts: list[MonthlyContractItem] = Field(default_factory=list)
    group_monthly_output: int = 0
    group_monthly_payable: int = 0
    group_cumulative_output: int = 0
    group_cumulative_payable: int = 0


class MonthlyListResponse(BaseModel):
    """月度台账列表响应"""
    project_id: uuid.UUID
    groups: list[MonthlyListGroup] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════
# 手动更新月度明细
# ═══════════════════════════════════════════════════════════════════

class MonthlyManualUpdate(BaseModel):
    """手动更新/创建月度台账明细（来源标记为 manual）"""
    detail_month: date = Field(..., description="月份（如 2026-01-01）")
    payment_amount: int | None = Field(None, ge=0, description="当月支付金额（分）")
    output_amount: int | None = Field(None, ge=0, description="当月产值（分）")
    est_cumulative_payable: int | None = Field(None, ge=0, description="预估累计应支付（分）")
    actual_cumulative_paid: int | None = Field(None, ge=0, description="实际累计已支付（分）")
    est_remaining_unpaid: int | None = Field(None, ge=0, description="预估剩余未支付（分）")
    cumulative_completed: int | None = Field(None, ge=0, description="累计已完成产值（分）")
    remaining_uncompleted: int | None = Field(None, ge=0, description="剩余未完成产值（分）")
    completed_ratio: float | None = Field(None, ge=0, le=1, description="已完比例")
    remaining_ratio: float | None = Field(None, ge=0, le=1, description="剩余未完比例")
    cost_items_detail: dict | None = Field(None, description="分项级产值明细")
    status: str = Field("confirmed", description="确认状态：pending/confirmed")
