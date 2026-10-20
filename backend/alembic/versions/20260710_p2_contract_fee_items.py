"""Phase2 #3 — 创建合同费用分项定义表 t_contract_fee_items

每份合同预先定义自己的费用分项（如施工合同有"建安工程费"+"安全文明施工费"）。
审核时以此为模板生成 t_review_fee_items 的快照值。

Revision ID: 20260710_p2_contract_fee_items
Revises: 20260710_p2_period_contracts
Create Date: 2026-07-10
"""

from typing import Union, Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "20260710_p2_contract_fee_items"
down_revision: Union[str, None] = "20260710_p2_period_contracts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "t_contract_fee_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), comment="主键"),
        sa.Column("contract_id", UUID(as_uuid=True), sa.ForeignKey("t_contracts.id"), nullable=False, index=True, comment="关联合同"),
        sa.Column("item_name", sa.String(100), nullable=False, comment="费用分项名称（如'建筑安装工程费'）"),
        sa.Column("contract_amount", sa.BigInteger(), server_default="0", comment="该分项的合同金额（分）"),
        sa.Column("current_ratio", sa.Numeric(6, 4), nullable=True, comment="当前期次付款比例（如 0.1000=10%）"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0", comment="排序序号"),
        sa.Column("remark", sa.Text(), nullable=True, comment="备注说明"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
    )


def downgrade() -> None:
    op.drop_table("t_contract_fee_items")
