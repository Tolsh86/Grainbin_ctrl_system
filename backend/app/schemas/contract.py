"""合同 Schema：请求/响应模型

Contract + ContractPaymentStage + NodeTemplate 的请求/响应定义。
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════
# 合同 Contract
# ═══════════════════════════════════════════════════════════════════

class ContractCreate(BaseModel):
    """创建合同"""
    contract_no: str = Field(..., min_length=1, max_length=20, description="合同编号（如 CX008）")
    supplier_name: str = Field(..., min_length=1, max_length=200, description="供应商/承包单位名称")
    contract_desc: str = Field(..., min_length=1, max_length=500, description="合同内容/类型描述")
    sign_date: date | None = Field(None, description="签订日期")
    contract_amount: int | None = Field(None, ge=0, description="合同金额（分）")
    contract_type: str = Field("secondary", description="合同类型：main(主合同)/secondary(二类费用)/supplementary(补充)")
    status: str = Field("active", description="状态：active(执行中)/expired(已到期)/terminated(已终止)")


class ContractUpdate(BaseModel):
    """更新合同 — 所有字段可选"""
    contract_no: str | None = Field(None, min_length=1, max_length=20, description="合同编号")
    supplier_name: str | None = Field(None, min_length=1, max_length=200, description="供应商名称")
    contract_desc: str | None = Field(None, min_length=1, max_length=500, description="合同内容描述")
    sign_date: date | None = Field(None, description="签订日期")
    contract_amount: int | None = Field(None, ge=0, description="合同金额（分）")
    contract_type: str | None = Field(None, description="合同类型")
    status: str | None = Field(None, description="状态")


class ContractResponse(BaseModel):
    """合同响应"""
    id: uuid.UUID
    project_id: uuid.UUID
    seq: int
    contract_no: str
    supplier_name: str
    contract_desc: str
    sign_date: date | None = None
    contract_amount: int | None = None
    contract_type: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContractDetailResponse(ContractResponse):
    """合同详情（含支付节点）"""
    payment_stages: list["PaymentStageResponse"] = Field(default_factory=list, description="支付节点列表")

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════
# 合同支付节点 ContractPaymentStage
# ═══════════════════════════════════════════════════════════════════

class PaymentStageCreate(BaseModel):
    """创建支付节点（手动添加）"""
    stage_order: int = Field(..., ge=0, description="阶段序号（1=施工前/预付款, 2=施工中, 3=竣工, 4=结算后, 5=质保尾款, 0=汇总行）")
    stage_name: str = Field(..., min_length=1, max_length=50, description="阶段名称")
    payment_terms: str | None = Field(None, description="支付条款原文")
    node_name: str | None = Field(None, max_length=100, description="节点名称（如'合同签订''竣工验收'）")
    agreed_ratio: float | None = Field(None, ge=0, le=1, description="约定支付比例（如 0.1000 = 10%）")
    agreed_amount: int | None = Field(None, ge=0, description="约定应支付金额（分）")
    planned_pay_date: date | None = Field(None, description="预计支付日期")


class PaymentStageUpdate(BaseModel):
    """更新支付节点 — 所有字段可选"""
    stage_order: int | None = Field(None, ge=0, description="阶段序号")
    stage_name: str | None = Field(None, min_length=1, max_length=50, description="阶段名称")
    payment_terms: str | None = Field(None, description="支付条款原文")
    node_name: str | None = Field(None, max_length=100, description="节点名称")
    agreed_ratio: float | None = Field(None, ge=0, le=1, description="约定支付比例")
    agreed_amount: int | None = Field(None, ge=0, description="约定应支付金额（分）")
    planned_pay_date: date | None = Field(None, description="预计支付日期")


class PaymentStageResponse(BaseModel):
    """支付节点响应"""
    id: uuid.UUID
    contract_id: uuid.UUID
    contract_no: str
    stage_order: int
    stage_name: str
    payment_terms: str | None = None
    node_name: str | None = None
    agreed_ratio: float | None = None
    agreed_amount: int | None = None
    planned_pay_date: date | None = None
    is_completed: bool = False
    completed_at: datetime | None = None
    cumulative_paid: int | None = None
    remaining_unpaid: int | None = None
    paid_ratio: float | None = None
    remaining_ratio: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════
# 节点模板 NodeTemplate
# ═══════════════════════════════════════════════════════════════════

class NodeTemplateCreate(BaseModel):
    """创建节点模板"""
    template_name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    biz_type: str = Field(..., max_length=30, description="业务类型: supervision/design/testing/construction/custom")
    description: str | None = Field(None, description="模板描述")
    stages: list[dict] = Field(..., min_length=1, description="节点配置数组")
    # stages: [{"order":1,"node_name":"合同签订","agreed_ratio":0.10,"trigger_condition":"签订后7日内","offset_days":7}, ...]


class NodeTemplateResponse(BaseModel):
    """节点模板响应"""
    id: uuid.UUID
    template_name: str
    biz_type: str
    description: str | None = None
    is_preset: bool = False
    stages: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════
# 节点生成（从模板创建）
# ═══════════════════════════════════════════════════════════════════

class NodesFromTemplateCreate(BaseModel):
    """从模板生成节点"""
    template_id: uuid.UUID = Field(..., description="模板 ID")
    contract_amount: int = Field(..., ge=0, description="合同金额（分），用于计算 agreed_amount")
    sign_date: date | None = Field(None, description="合同签订日期，用于计算 planned_pay_date")


class NodeGeneratePreview(BaseModel):
    """节点生成预览（响应中的一条）"""
    stage_order: int
    stage_name: str
    node_name: str
    agreed_ratio: float
    agreed_amount: int
    planned_pay_date: date | None = None
    trigger_condition: str | None = None
