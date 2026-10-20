"""V2.3 — 删除 fee_items 和 fee_item_id 字段

fee_items（t_contracts）和 fee_item_id（t_contract_payment_stages）是早期
"单合同内分项"设计的遗留字段。现在统一为 N 条 Contract 记录 + contract_no 归组模式，
每条记录本身即一个结算单元，不再需要分项明细。

Revision ID: 20260709_drop_fee_items
Revises: 20260707_fix_contract_no_idx
Create Date: 2026-07-09

变更:
1. t_contracts               — 删除 fee_items (JSONB)
2. t_contract_payment_stages — 删除 fee_item_id (UUID)
3. t_contract_monthly_detail — cost_items_detail JSONB 保留（历史快照数据，与 fee_items 无关）
"""

from typing import Union, Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision: str = "20260709_drop_fee_items"
down_revision: Union[str, None] = "20260707_fix_contract_no_idx"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("t_contracts", "fee_items")
    op.drop_column("t_contract_payment_stages", "fee_item_id")


def downgrade() -> None:
    op.add_column(
        "t_contracts",
        sa.Column("fee_items", JSONB(), nullable=True, comment="费用分项明细"),
    )
    op.add_column(
        "t_contract_payment_stages",
        sa.Column("fee_item_id", UUID(as_uuid=True), nullable=True, comment="关联费用分项ID"),
    )
