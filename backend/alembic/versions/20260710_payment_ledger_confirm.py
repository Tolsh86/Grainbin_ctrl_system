"""V2.2 — t_contract_payments 新增台账分组 + 确认审核字段

变更：
1. payment_type      — 支付类型：advance(预付款)/progress(进度款)/settlement(结算款)/retention(质保金)
2. ledger_group      — 台账分组（冗余自合同）
3. confirm_status    — 确认状态：pending(待确认)/confirmed(已确认)/rejected(已驳回)，默认 pending
4. confirmed_at      — 确认时间
5. confirmed_by      — 确认人用户ID
6. confirm_remark    — 确认/驳回备注
7. ledger_group 索引 — 按台账分组查询加速

Revision ID: 20260710_payment_ledger_confirm
Revises: 20260709_period_to_dates
Create Date: 2026-07-10
"""

from typing import Union, Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "20260710_payment_ledger_confirm"
down_revision: Union[str, None] = "20260709_period_to_dates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 新增支付类型
    op.add_column(
        "t_contract_payments",
        sa.Column("payment_type", sa.String(30), nullable=True, comment="支付类型：advance(预付款)/progress(进度款)/settlement(结算款)/retention(质保金)"),
    )

    # 2. 新增台账分组
    op.add_column(
        "t_contract_payments",
        sa.Column("ledger_group", sa.String(20), nullable=True, comment="台账分组（冗余自合同）"),
    )

    # 3. 新增确认状态（非空，默认 pending）
    op.add_column(
        "t_contract_payments",
        sa.Column("confirm_status", sa.String(20), nullable=False, server_default="pending", comment="确认状态：pending(待确认)/confirmed(已确认)/rejected(已驳回)"),
    )

    # 4. 新增确认时间
    op.add_column(
        "t_contract_payments",
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True, comment="确认时间"),
    )

    # 5. 新增确认人
    op.add_column(
        "t_contract_payments",
        sa.Column("confirmed_by", UUID(as_uuid=True), nullable=True, comment="确认人用户ID"),
    )

    # 6. 新增确认备注
    op.add_column(
        "t_contract_payments",
        sa.Column("confirm_remark", sa.Text(), nullable=True, comment="确认/驳回备注"),
    )

    # 7. 台账分组查询索引
    op.create_index(
        "ix_t_contract_payments_ledger_group",
        "t_contract_payments",
        ["ledger_group"],
        postgresql_using="btree",
    )


def downgrade() -> None:
    op.drop_index("ix_t_contract_payments_ledger_group", table_name="t_contract_payments")
    op.drop_column("t_contract_payments", "confirm_remark")
    op.drop_column("t_contract_payments", "confirmed_by")
    op.drop_column("t_contract_payments", "confirmed_at")
    op.drop_column("t_contract_payments", "confirm_status")
    op.drop_column("t_contract_payments", "ledger_group")
    op.drop_column("t_contract_payments", "payment_type")
