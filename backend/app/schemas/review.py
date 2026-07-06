"""进度款审核 Schema：请求/响应模型

与 t_progress_payment_review 模型字段完全对齐（V2.2）。
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    """创建进度款审核记录"""
    contract_id: uuid.UUID | None = Field(None, description="关联合同 ID（可选）")
    review_type: str = Field(..., max_length=20, description="审核类型（自由文本）：施工单位/设备单位/设计单位/监理过控/...")
    period_month: str = Field(..., max_length=50, description="期数/月份（如'第一期/2026年01月'）")
    period_no: int = Field(1, ge=1, description="期次编号")
    applicant_unit: str = Field(..., max_length=200, description="申请单位（从供应商带出，可修改）")

    # 通用金额字段（单位：分）
    contract_amount: int = Field(0, ge=0, description="合同金额（分）")
    cumulative_reported_output: int = Field(0, ge=0, description="累计报送产值（分）")
    payment_ratio: float | None = Field(None, ge=0, le=1, description="付款比例（如 0.2=20%）")
    current_audited_output: int = Field(0, ge=0, description="本期审核产值（分）")
    cumulative_audited_output: int = Field(0, ge=0, description="累计审核产值（分）")
    cumulative_audited_payable: int = Field(0, ge=0, description="累计审核应付款（分）")

    # 施工类特有
    constr_install_fee: int | None = Field(None, ge=0, description="建筑安装工程费（分）")
    safety_civil_fee: int | None = Field(None, ge=0, description="安全文明施工费（分）")
    constr_install_pay_ratio: float | None = Field(None, ge=0, le=1, description="建安工程费付款比例")
    safety_civil_pay_ratio: float | None = Field(None, ge=0, le=1, description="安全文明施工费付款比例")

    # 监理过控类特有
    supervision_fee: int | None = Field(None, ge=0, description="工程监理服务费（分）")
    cost_consult_fee: int | None = Field(None, ge=0, description="造价咨询服务费（分）")
    settlement_fee: int | None = Field(None, ge=0, description="竣工结算服务费（分）")
    supervision_pay_ratio: float | None = Field(None, ge=0, le=1, description="监理服务费付款比例")
    cost_consult_pay_ratio: float | None = Field(None, ge=0, le=1, description="造价咨询费付款比例")
    settlement_pay_ratio: float | None = Field(None, ge=0, le=1, description="结算服务费付款比例")

    # 动态字段
    extra_fields: dict | None = Field(None, description="审核类型特有的动态字段（JSONB）")
    remark: str | None = Field(None, description="备注")
    tax_rate: float | None = Field(None, ge=0, le=100, description="税率（如 9.00=9%）")
    submit_date: date | None = Field(None, description="申报日期")


class ReviewUpdate(BaseModel):
    """更新审核记录 — 所有字段可选"""
    review_type: str | None = Field(None, max_length=20, description="审核类型")
    period_month: str | None = Field(None, max_length=50, description="期数/月份")
    period_no: int | None = Field(None, ge=1, description="期次编号")
    applicant_unit: str | None = Field(None, max_length=200, description="申请单位")
    contract_amount: int | None = Field(None, ge=0, description="合同金额（分）")
    cumulative_reported_output: int | None = Field(None, ge=0, description="累计报送产值（分）")
    payment_ratio: float | None = Field(None, ge=0, le=1, description="付款比例")
    current_audited_output: int | None = Field(None, ge=0, description="本期审核产值（分）")
    cumulative_audited_output: int | None = Field(None, ge=0, description="累计审核产值（分）")
    cumulative_audited_payable: int | None = Field(None, ge=0, description="累计审核应付款（分）")
    constr_install_fee: int | None = Field(None, ge=0, description="建筑安装工程费")
    safety_civil_fee: int | None = Field(None, ge=0, description="安全文明施工费")
    constr_install_pay_ratio: float | None = Field(None, ge=0, le=1, description="建安工程费付款比例")
    safety_civil_pay_ratio: float | None = Field(None, ge=0, le=1, description="安全文明施工费付款比例")
    supervision_fee: int | None = Field(None, ge=0, description="工程监理服务费")
    cost_consult_fee: int | None = Field(None, ge=0, description="造价咨询服务费")
    settlement_fee: int | None = Field(None, ge=0, description="竣工结算服务费")
    supervision_pay_ratio: float | None = Field(None, ge=0, le=1, description="监理服务费付款比例")
    cost_consult_pay_ratio: float | None = Field(None, ge=0, le=1, description="造价咨询费付款比例")
    settlement_pay_ratio: float | None = Field(None, ge=0, le=1, description="结算服务费付款比例")
    extra_fields: dict | None = Field(None, description="动态字段")
    remark: str | None = Field(None, description="备注")
    tax_rate: float | None = Field(None, ge=0, le=100, description="税率")
    submit_date: date | None = Field(None, description="申报日期")


class ReviewStatusUpdate(BaseModel):
    """审核状态更新"""
    audit_status: str = Field(..., description="审核状态：pending(待审)/auditing(审核中)/audited(已审)/paid(已付)")
    audited_by: uuid.UUID | None = Field(None, description="审核人 ID（audited/paid 时建议填写）")


class ReviewResponse(BaseModel):
    """进度款审核响应"""
    id: uuid.UUID
    project_id: uuid.UUID
    contract_id: uuid.UUID | None = None

    # 审核标识
    review_type: str
    period_month: str
    period_no: int
    applicant_unit: str

    # 通用金额字段
    contract_amount: int
    cumulative_reported_output: int
    payment_ratio: float | None = None
    current_audited_output: int
    cumulative_audited_output: int
    cumulative_audited_payable: int

    # 施工类特有
    constr_install_fee: int | None = None
    safety_civil_fee: int | None = None
    constr_install_pay_ratio: float | None = None
    safety_civil_pay_ratio: float | None = None

    # 监理过控类特有
    supervision_fee: int | None = None
    cost_consult_fee: int | None = None
    settlement_fee: int | None = None
    supervision_pay_ratio: float | None = None
    cost_consult_pay_ratio: float | None = None
    settlement_pay_ratio: float | None = None

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

    model_config = {"from_attributes": True}
