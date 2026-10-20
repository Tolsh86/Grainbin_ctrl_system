"""费用分项 Schema：请求/响应模型 (Phase2)

t_contract_fee_items — 合同费用分项定义（模板）
t_review_fee_items — 审核费用分项值（快照）
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════
# 合同费用分项定义（模板）
# ═══════════════════════════════════════════════════════════════════

class ContractFeeItemCreate(BaseModel):
    """费用分项模板 — 创建"""
    item_name: str = Field(..., max_length=100, description="费用分项名称")
    contract_amount: int | None = Field(None, ge=0, description="该分项的合同金额（分）")
    current_ratio: float | None = Field(None, ge=0, le=1, description="当前期次付款比例（如 0.1000=10%）")
    sort_order: int = Field(0, ge=0, description="排序序号")
    remark: str | None = Field(None, description="备注")


class ContractFeeItemUpdate(BaseModel):
    """费用分项模板 — 更新（所有字段可选）"""
    item_name: str | None = Field(None, max_length=100, description="费用分项名称")
    contract_amount: int | None = Field(None, ge=0, description="分项合同金额（分）")
    current_ratio: float | None = Field(None, ge=0, le=1, description="付款比例")
    sort_order: int | None = Field(None, ge=0, description="排序序号")
    remark: str | None = Field(None, description="备注")


class ContractFeeItemResponse(BaseModel):
    """费用分项模板 — 响应"""
    id: uuid.UUID
    contract_id: uuid.UUID
    item_name: str
    contract_amount: int | None = None
    current_ratio: float | None = None
    sort_order: int
    remark: str | None = None

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════
# 审核费用分项值（快照）
# ═══════════════════════════════════════════════════════════════════

class ReviewFeeItemCreate(BaseModel):
    """审核费用分项 — 创建（从模板快照生成）"""
    fee_item_id: uuid.UUID | None = Field(None, description="关联的费用分项模板 ID")
    item_name: str = Field(..., max_length=100, description="快照：费用分项名称")
    payment_ratio: float | None = Field(None, ge=0, le=1, description="快照：本期付款比例")
    reported_amount: int | None = Field(None, ge=0, description="报送金额（分）")
    reviewed_amount: int | None = Field(None, ge=0, description="审定金额（分）")
    remark: str | None = Field(None, description="备注")


class ReviewFeeItemUpdate(BaseModel):
    """审核费用分项 — 更新（需 id 匹配，报送值和审定值均可编辑）"""
    id: uuid.UUID | None = Field(None, description="费用分项记录 ID（用于匹配更新）")
    reported_amount: int | None = Field(None, ge=0, description="报送金额（分）")
    reviewed_amount: int | None = Field(None, ge=0, description="审定金额（分）")
    remark: str | None = Field(None, description="备注")


class ReviewFeeItemResponse(BaseModel):
    """审核费用分项 — 响应"""
    id: uuid.UUID
    review_id: uuid.UUID
    fee_item_id: uuid.UUID | None = None
    item_name: str
    payment_ratio: float | None = None
    reported_amount: int | None = None
    reviewed_amount: int | None = None
    remark: str | None = None

    model_config = {"from_attributes": True}
