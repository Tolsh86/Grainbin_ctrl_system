"""Phase2 #5 — 改造 t_progress_payment_review

1. DELETE FROM 清空历史测试数据
2. DROP 13 个硬编码列 (period_month, period_no, payment_ratio, 10 个费用/比例列)
3. ADD period_id UUID NOT NULL (FK → t_reporting_periods)
4. ALTER contract_id SET NOT NULL
5. ALTER audit_status SET DEFAULT 'draft'

Revision ID: 20260710_p2_refactor_review
Revises: 20260710_p2_review_fee_items
Create Date: 2026-07-10
"""

from typing import Union, Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "20260710_p2_refactor_review"
down_revision: Union[str, None] = "20260710_p2_review_fee_items"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 要删除的 13 个列
COLS_TO_DROP = [
    "period_month",
    "period_no",
    "payment_ratio",
    "constr_install_fee",
    "safety_civil_fee",
    "constr_install_pay_ratio",
    "safety_civil_pay_ratio",
    "supervision_fee",
    "cost_consult_fee",
    "settlement_fee",
    "supervision_pay_ratio",
    "cost_consult_pay_ratio",
    "settlement_pay_ratio",
]


def upgrade() -> None:
    # 1. 清空历史测试数据
    op.execute("DELETE FROM t_progress_payment_review")

    # 2. 删除 13 个硬编码列
    for col in COLS_TO_DROP:
        op.drop_column("t_progress_payment_review", col)

    # 3. 新增 period_id（NOT NULL + FK + INDEX）
    op.add_column(
        "t_progress_payment_review",
        sa.Column("period_id", UUID(as_uuid=True), nullable=False, comment="关联期次"),
    )
    op.create_foreign_key(
        "fk_progress_review_period",
        "t_progress_payment_review", "t_reporting_periods",
        ["period_id"], ["id"],
    )
    op.create_index("ix_t_progress_payment_review_period_id", "t_progress_payment_review", ["period_id"])

    # 4. contract_id 改为 NOT NULL
    op.alter_column("t_progress_payment_review", "contract_id", nullable=False)

    # 5. audit_status default 改为 'draft'
    op.alter_column("t_progress_payment_review", "audit_status", server_default="draft")


def downgrade() -> None:
    # 1. 恢复 audit_status default
    op.alter_column("t_progress_payment_review", "audit_status", server_default="pending")

    # 2. 恢复 contract_id 为 nullable
    op.alter_column("t_progress_payment_review", "contract_id", nullable=True)

    # 3. 删除 period_id 相关
    op.drop_index("ix_t_progress_payment_review_period_id", table_name="t_progress_payment_review")
    op.drop_constraint("fk_progress_review_period", "t_progress_payment_review", type_="foreignkey")
    op.drop_column("t_progress_payment_review", "period_id")

    # 4. 恢复 13 个硬编码列
    op.add_column("t_progress_payment_review", sa.Column("period_month", sa.String(50), nullable=False, comment="期数/月份"))
    op.add_column("t_progress_payment_review", sa.Column("period_no", sa.Integer(), nullable=False, server_default="1", comment="期次编号"))
    op.add_column("t_progress_payment_review", sa.Column("payment_ratio", sa.Numeric(6, 4), nullable=True, comment="付款比例"))
    op.add_column("t_progress_payment_review", sa.Column("constr_install_fee", sa.BigInteger(), server_default="0", comment="建筑安装工程费（分）"))
    op.add_column("t_progress_payment_review", sa.Column("safety_civil_fee", sa.BigInteger(), server_default="0", comment="安全文明施工费（分）"))
    op.add_column("t_progress_payment_review", sa.Column("constr_install_pay_ratio", sa.Numeric(6, 4), nullable=True, comment="建筑安装工程费付款比例"))
    op.add_column("t_progress_payment_review", sa.Column("safety_civil_pay_ratio", sa.Numeric(6, 4), nullable=True, comment="安全文明施工费付款比例"))
    op.add_column("t_progress_payment_review", sa.Column("supervision_fee", sa.BigInteger(), server_default="0", comment="工程监理服务费（分）"))
    op.add_column("t_progress_payment_review", sa.Column("cost_consult_fee", sa.BigInteger(), server_default="0", comment="造价咨询服务费（分）"))
    op.add_column("t_progress_payment_review", sa.Column("settlement_fee", sa.BigInteger(), server_default="0", comment="竣工结算服务费（分）"))
    op.add_column("t_progress_payment_review", sa.Column("supervision_pay_ratio", sa.Numeric(6, 4), nullable=True, comment="工程监理服务费付款比例"))
    op.add_column("t_progress_payment_review", sa.Column("cost_consult_pay_ratio", sa.Numeric(6, 4), nullable=True, comment="造价咨询服务费付款比例"))
    op.add_column("t_progress_payment_review", sa.Column("settlement_pay_ratio", sa.Numeric(6, 4), nullable=True, comment="竣工结算服务费付款比例"))
