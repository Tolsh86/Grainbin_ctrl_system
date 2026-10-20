"""V2.2 — contract_sub_type → review_mode + ledger_group

Revision ID: 20260707_subtype_to_review_mode
Revises: 20260707_drop_contract_no_unique
Create Date: 2026-07-07

变更:
1. t_contracts.contract_sub_type → review_mode (审核模式: daily_aggregate/node_judge/none)
2. t_contracts 新增 ledger_group (台账分组: construction/equipment/service/none)
"""

from typing import Union, Sequence
from alembic import op
import sqlalchemy as sa


revision: str = "20260707_subtype_to_review_mode"
down_revision: Union[str, None] = "20260707_drop_contract_no_unique"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 重命名 contract_sub_type → review_mode
    op.alter_column(
        "t_contracts",
        "contract_sub_type",
        new_column_name="review_mode",
        existing_type=sa.String(50),
        existing_nullable=True,
        comment="审核模式: daily_aggregate(日报聚合)/node_judge(节点判断)/none(无产值)",
        server_default=sa.text("'daily_aggregate'"),
    )

    # 2. 新增 ledger_group
    op.add_column(
        "t_contracts",
        sa.Column(
            "ledger_group",
            sa.String(20),
            nullable=True,
            comment="台账分组: construction(建安合计)/equipment(设备合计)/service(二类费用合计)/none(不计入台账)",
        ),
    )


def downgrade() -> None:
    # 2. 删除 ledger_group
    op.drop_column("t_contracts", "ledger_group")

    # 1. 重命名回 contract_sub_type
    op.alter_column(
        "t_contracts",
        "review_mode",
        new_column_name="contract_sub_type",
        existing_type=sa.String(50),
        existing_nullable=True,
        comment="合同分项类型",
        server_default=sa.text("'construction'"),
    )
