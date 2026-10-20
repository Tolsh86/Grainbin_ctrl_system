"""审核工作台 Schema：请求/响应模型

接口：
- GET  /audit/summary                     → AuditSummaryResponse
- GET  /audit/contract/{contract_id}       → ConstructionAuditResponse | ConsultingAuditResponse
- POST /audit/confirm                     → AuditConfirmRequest → MonthlyDetailResponse
"""

from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════
# 概览
# ═══════════════════════════════════════════════════════════════════

class AuditSummaryResponse(BaseModel):
    """当月合同审核概览"""
    total_contracts: int = Field(0, description="项目下合同总数")
    pending_count: int = Field(0, description="当月待审合同数（status=pending）")
    confirmed_count: int = Field(0, description="当月已审合同数（status=confirmed）")


# ═══════════════════════════════════════════════════════════════════
# 建安合同 — 日报聚合分项
# ═══════════════════════════════════════════════════════════════════

class ConstructionAggItem(BaseModel):
    """建安合同日报聚合 — 单个分项"""
    category: str | None = None
    cost_sub_type: str | None = None
    item_name: str | None = None
    unit: str | None = None
    unit_price: int | None = None
    total_quantity: int = 0
    total_amount: int = 0
    row_count: int = 0


class ConstructionAuditResponse(BaseModel):
    """建安合同审核详情"""
    contract_id: uuid.UUID
    contract_no: str
    review_mode: str | None = None
    contract_amount: int | None = None
    detail_month: date
    items: list[ConstructionAggItem] = Field(default_factory=list)
    total_output: int = 0
    total_payable: int = 0


# ═══════════════════════════════════════════════════════════════════
# 咨询合同 — 单条合同即费用分项，聚合节点累计产值
# ═══════════════════════════════════════════════════════════════════

class ConsultingFeeNode(BaseModel):
    """咨询合同 — 单条合同下的支付节点累计"""
    node_name: str | None = None
    stage_order: int = 0
    stage_name: str | None = None
    agreed_ratio: float | None = None
    agreed_amount: int | None = None
    reported_amount: int | None = None
    reviewed_amount: int | None = None
    is_completed: bool = False
    triggered_at: date | None = None


class ConsultingFeeItemDetail(BaseModel):
    """咨询合同 — 单条合同记录（即一个结算单元）及其节点累计"""
    fee_item_id: str = ""
    name: str = ""
    contract_amount: int | None = None
    agreed_ratio: float | None = None
    nodes: list[ConsultingFeeNode] = Field(default_factory=list)
    cumulative_reported: int = 0
    cumulative_reviewed: int = 0


class ConsultingAuditResponse(BaseModel):
    """咨询合同审核详情"""
    contract_id: uuid.UUID
    contract_no: str
    review_mode: str | None = None
    contract_amount: int | None = None
    detail_month: date
    fee_items: list[ConsultingFeeItemDetail] = Field(default_factory=list)
    total_reported: int = 0
    total_reviewed: int = 0


# ═══════════════════════════════════════════════════════════════════
# 审核确认
# ═══════════════════════════════════════════════════════════════════

class AuditConfirmItem(BaseModel):
    """审核确认 — 单个分项审定数据"""
    fee_item_id: str = Field(..., description="分项 ID（咨询合同审计时可为空，表示合同本身）")
    name: str = Field(..., description="分项名称")
    output: int = Field(..., ge=0, description="审定产值（分）")
    ratio: float = Field(..., ge=0, le=1, description="本次支付比例")
    payable: int = Field(..., ge=0, description="本次应付金额（分）")


class AuditConfirmRequest(BaseModel):
    """审核确认请求"""
    contract_id: uuid.UUID = Field(..., description="关联合同 ID")
    detail_month: date = Field(..., description="审核月份（如 2026-01-01）")
    items: list[AuditConfirmItem] = Field(..., min_length=1, description="分项审定数据列表")
    status: str = Field("confirmed", description="确认状态：confirmed")
