"""V2.1 — 合同支付记录表 + 校验状态字段

Revision ID: 20260703_v2_1_payments
Revises: 20260703_v2_initial
Create Date: 2026-07-03

新增:
- t_contract_payments: 逐笔支付记录（支撑支付台账、对账报告）
- t_ingest_rows.validation_status: normal/warning/error/suspicious
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '20260703_v2_1_payments'
down_revision: Union[str, None] = '20260703_v2_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════════════
    # 1. t_contract_payments — 逐笔支付记录
    # ═══════════════════════════════════════════════════════════════
    op.create_table(
        "t_contract_payments",
        sa.Column("id", postgresql.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("contract_id", postgresql.UUID, sa.ForeignKey("t_contracts.id"), nullable=False, index=True, comment="关联合同"),
        sa.Column("contract_no", sa.String(20), nullable=False, index=True, comment="冗余 contract_no"),
        sa.Column("stage_id", postgresql.UUID, sa.ForeignKey("t_contract_payment_stages.id"), index=True, comment="关联支付节点（可选）"),
        sa.Column("payment_date", sa.Date, nullable=False, comment="实际支付日期"),
        sa.Column("payment_amount", sa.BigInteger, nullable=False, server_default="0", comment="本次支付金额（分）"),
        sa.Column("payment_voucher", sa.String(500), comment="支付凭证（文件路径或编号）"),
        sa.Column("payer", sa.String(200), comment="付款方"),
        sa.Column("payee", sa.String(200), comment="收款方"),
        sa.Column("remark", sa.Text, comment="备注"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False, comment="更新时间"),
        comment="合同逐笔支付记录（V2.1）",
    )
    op.create_index("ix_contract_payments_date", "t_contract_payments", ["contract_id", "payment_date"])
    op.create_index("ix_contract_payments_no", "t_contract_payments", ["contract_no"])


def downgrade() -> None:
    op.drop_index("ix_contract_payments_date")
    op.drop_index("ix_contract_payments_no")
    op.drop_table("t_contract_payments")
