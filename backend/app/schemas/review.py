"""进度款审核 Schema：请求/响应模型 (Phase2 改造)

Phase2 变更：
- 删除 period_month, period_no, payment_ratio, 9 个硬编码费用/比例字段
- 新增 period_id（必填）
- contract_id 改为必填
- 新增 fee_items 嵌套列表
- audit_status 默认值对齐 draft/submitted/reviewed
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.fee_item import ReviewFeeItemCreate, ReviewFeeItemUpdate, ReviewFeeItemResponse


class ReviewCreate(BaseModel):
    """创建进度款审核记录"""
    contract_id: uuid.UUID = Field(..., description="关联合同 ID（必填）")
    period_id: uuid.UUID = Field(..., description="关联期次 ID（必填）")
    review_type: str = Field(..., max_length=20, description="审核类型：设备/设计/施工/监理过控")
    applicant_unit: str = Field(..., max_length=200, description="申请单位")

    # 通用金额字段（单位：分）
    contract_amount: int = Field(0, ge=0, description="合同金额（分）")
    cumulative_reported_output: int = Field(0, ge=0, description="累计报送产值（分）")
    current_audited_output: int = Field(0, ge=0, description="本期审定产值（分）")
    cumulative_audited_output: int = Field(0, ge=0, description="累计审定产值（分）")
    cumulative_audited_payable: int = Field(0, ge=0, description="累计审定应付款（分）")

    # 动态字段
    extra_fields: dict | None = Field(None, description="审核类型特有的动态字段（JSONB）")
    remark: str | None = Field(None, description="备注")
    tax_rate: float | None = Field(None, ge=0, le=100, description="税率（如 9.00=9%）")
    submit_date: date | None = Field(None, description="申报日期")

    # 费用分项明细
    fee_items: list[ReviewFeeItemCreate] = Field(
        default_factory=list,
        description="费用分项列表（从合同模板复制生成）"
    )


class ReviewUpdate(BaseModel):
    """更新审核记录 — 所有字段可选，支持嵌套费用分项值更新。"""
    review_type: str | None = Field(None, max_length=20, description="审核类型")
    applicant_unit: str | None = Field(None, max_length=200, description="申请单位")
    contract_amount: int | None = Field(None, ge=0, description="合同金额（分）")
    cumulative_reported_output: int | None = Field(None, ge=0, description="累计报送产值（分）")
    current_audited_output: int | None = Field(None, ge=0, description="本期审定产值（分）")
    cumulative_audited_output: int | None = Field(None, ge=0, description="累计审定产值（分）")
    cumulative_audited_payable: int | None = Field(None, ge=0, description="累计审定应付款（分）")
    extra_fields: dict | None = Field(None, description="动态字段")
    remark: str | None = Field(None, description="备注")
    tax_rate: float | None = Field(None, ge=0, le=100, description="税率")
    submit_date: date | None = Field(None, description="申报日期")
    # 费用分项值更新（报送值和审定值共用此接口）
    fee_items: list[ReviewFeeItemUpdate] | None = Field(
        None, description="费用分项列表（按 id 匹配更新，报送/审定金额分别填写）"
    )


class ReviewStatusUpdate(BaseModel):
    """审核状态更新（Phase2：对齐 draft/submitted/reviewed）"""
    audit_status: str = Field(..., description="审核状态：draft(草稿)/submitted(已报送)/reviewed(已审核)")


class ReviewResponse(BaseModel):
    """进度款审核响应"""
    id: uuid.UUID
    project_id: uuid.UUID
    contract_id: uuid.UUID
    period_id: uuid.UUID

    # 审核标识
    review_type: str
    applicant_unit: str

    # 通用金额字段
    contract_amount: int
    cumulative_reported_output: int
    current_audited_output: int
    cumulative_audited_output: int
    cumulative_audited_payable: int

    # 动态字段
    extra_fields: dict | None = None
    remark: str | None = None
    tax_rate: float | None = None

    # 审核状态
    audit_status: str
    submit_date: date | None = None
    audited_by: uuid.UUID | None = None
    audited_at: datetime | None = None

    # 时间戳
    created_at: datetime
    updated_at: datetime

    # 费用分项明细
    fee_items: list[ReviewFeeItemResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}
