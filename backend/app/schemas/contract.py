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
    # ── V2.2 第二阶段新增 ──
    contract_group: str | None = Field(None, max_length=50, description="合同编号组，用于归组同项目下多份独立合同")
    review_mode: str = Field("daily_aggregate", max_length=20, description="审核模式：daily_aggregate(日报聚合)/node_judge(节点判断)/none(无产值)")
    ledger_group: str = Field("service", max_length=20, description="台账分组：construction(建安合计)/equipment(设备合计)/service(二类费用合计)/none(不计入台账)")


class ContractUpdate(BaseModel):
    """更新合同 — 所有字段可选"""
    contract_no: str | None = Field(None, min_length=1, max_length=20, description="合同编号")
    supplier_name: str | None = Field(None, min_length=1, max_length=200, description="供应商名称")
    contract_desc: str | None = Field(None, min_length=1, max_length=500, description="合同内容描述")
    sign_date: date | None = Field(None, description="签订日期")
    contract_amount: int | None = Field(None, ge=0, description="合同金额（分）")
    contract_type: str | None = Field(None, description="合同类型")
    status: str | None = Field(None, description="状态")
    # ── V2.2 第二阶段新增 ──
    contract_group: str | None = Field(None, max_length=50, description="合同编号组")
    review_mode: str | None = Field(None, max_length=20, description="审核模式")
    ledger_group: str | None = Field(None, max_length=20, description="台账分组")


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
    # ── V2.2 第二阶段新增 ──
    contract_group: str | None = None
    review_mode: str | None = None
    ledger_group: str | None = None
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
    """创建支付节点（手动添加）

    阶段序号(stage_order)由后端自动排列(max+1)，约定金额(agreed_amount)由后端自动计算(合同金额×比例)。
    报送产值/审定产值/触发时间属于审核环节，不在节点创建时填写。
    """
    stage_name: str = Field(..., min_length=1, max_length=50, description="阶段名称（如：施工前/预付款）")
    payment_terms: str | None = Field(None, description="支付条款原文（如：合同签订后7日内支付）")
    node_name: str | None = Field(None, max_length=100, description="节点名称（如：合同签订、竣工验收）")
    agreed_ratio: float | None = Field(None, ge=0, le=1, description="约定支付比例（如 0.1000 = 10%）")
    planned_pay_date: date | None = Field(None, description="预计支付日期（须 >= 合同签订日期）")


class PaymentStageUpdate(BaseModel):
    """更新支付节点 — 所有字段可选

    agreed_amount 由后端自动重算（合同金额×比例）。报送产值/审定产值/触发时间属于审核环节，不在此编辑。
    阶段序号(stage_order)由后端自动管理，不可手动调整。
    """
    stage_name: str | None = Field(None, min_length=1, max_length=50, description="阶段名称")
    payment_terms: str | None = Field(None, description="支付条款原文")
    node_name: str | None = Field(None, max_length=100, description="节点名称")
    agreed_ratio: float | None = Field(None, ge=0, le=1, description="约定支付比例")
    planned_pay_date: date | None = Field(None, description="预计支付日期")


class PaymentStageResponse(BaseModel):
    """支付节点响应"""
    id: uuid.UUID
    contract_id: uuid.UUID
    contract_no: str
    # 合同冗余字段（查询项目级节点时填充，方便表格展示）
    supplier_name: str | None = None
    contract_desc: str | None = None
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
    # ── V2.2 第二阶段新增（审核环节填充，节点创建时不可填）──
    triggered_at: date | None = None
    reported_amount: int | None = None
    reviewed_amount: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════
# 合同月度明细 ContractMonthlyDetail (V2.2 新增响应模型)
# ═══════════════════════════════════════════════════════════════════

class MonthlyDetailCreate(BaseModel):
    """创建月度明细"""
    contract_id: uuid.UUID = Field(..., description="关联合同ID")
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
    # ── V2.2 第二阶段新增 ──
    source: str = Field("auto", description="数据来源：auto(系统汇总)/manual(人工审定)")
    status: str = Field("pending", description="确认状态：pending/confirmed")
    cost_items_detail: dict | None = Field(None, description="分项级产值明细 {items: [{fee_item_id, name, output, ratio, payable}]}")


class MonthlyDetailResponse(BaseModel):
    """月度明细响应"""
    id: uuid.UUID
    contract_id: uuid.UUID
    contract_no: str
    detail_month: date
    payment_amount: int | None = None
    output_amount: int | None = None
    est_cumulative_payable: int | None = None
    actual_cumulative_paid: int | None = None
    est_remaining_unpaid: int | None = None
    cumulative_completed: int | None = None
    remaining_uncompleted: int | None = None
    completed_ratio: float | None = None
    remaining_ratio: float | None = None
    # ── V2.2 第二阶段新增 ──
    source: str = "auto"
    status: str = "pending"
    cost_items_detail: dict | None = None
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
    stages: list[dict] | dict
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


class ContractGroupResponse(BaseModel):
    """合同分组响应"""
    contract_group: str
    contracts: list[ContractResponse]


# ═══════════════════════════════════════════════════════════════════
# 月度付款矩阵 (V2.2)
# ═══════════════════════════════════════════════════════════════════

class PaymentMatrixNode(BaseModel):
    """矩阵中的节点摘要"""
    node_name: str | None = None
    stage_name: str
    agreed_amount: int | None = None  # 分
    agreed_ratio: float | None = None
    planned_pay_date: date | None = None
    is_completed: bool = False

    model_config = {"from_attributes": True}


class PaymentMatrixContract(BaseModel):
    """矩阵中的合同卡片"""
    contract_id: uuid.UUID
    supplier_name: str
    contract_desc: str
    contract_amount: int | None = None  # 分
    sign_date: date | None = None
    review_mode: str | None = None
    nodes: list[PaymentMatrixNode] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class PaymentMatrixGroup(BaseModel):
    """按 contract_no 分组的合同集合"""
    contract_no: str
    total_amount: int = 0  # 分（含节点的合同金额总和）
    contracts: list[PaymentMatrixContract] = Field(default_factory=list)


class PaymentMatrixResponse(BaseModel):
    """月度付款矩阵完整响应"""
    project_name: str
    month_range: list[str] = Field(default_factory=list, description="月份列表 ['2025-06','2025-07',...]")
    monthly_totals: dict[str, float] = Field(default_factory=dict, description="{'2025-06':120000.50,...} 元")
    groups: list[PaymentMatrixGroup] = Field(default_factory=list)
