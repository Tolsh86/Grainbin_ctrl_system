"""V2.2 Refactor — t_contract_payments 精简重构

变更：
1. DROP: payment_date, payment_amount, payer, payee — 原支付信息字段
2. DROP: payment_type, confirm_status, confirmed_by, confirm_remark — 上一版 V2.2 字段
3. ADD: reported_amount  (BIGINT NOT NULL DEFAULT 0)  — 报送金额
4. ADD: approved_amount (BIGINT NOT NULL DEFAULT 0)  — 批准金额
5. ADD: status         (VARCHAR(20) NOT NULL DEFAULT 'pending') — pending/confirmed/rejected
6. ADD: reject_reason  (TEXT)  — 驳回原因
7. KEEP: confirmed_at  — 确认时间（上一版已加）
8. KEEP: ledger_group  — 台账分组（上一版已加）

Revision ID: 20260710_payment_model_refactor
Revises: 20260710_payment_ledger_confirm
Create Date: 2026-07-10
"""

from typing import Union, Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "20260710_payment_model_refactor"
down_revision: Union[str, None] = "20260710_payment_ledger_confirm"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 删除旧字段 ──
    op.drop_column("t_contract_payments", "payment_date")
    op.drop_column("t_contract_payments", "payment_amount")
    op.drop_column("t_contract_payments", "payer")
    op.drop_column("t_contract_payments", "payee")
    op.drop_column("t_contract_payments", "payment_type")
    op.drop_column("t_contract_payments", "confirm_status")
    op.drop_column("t_contract_payments", "confirmed_by")
    op.drop_column("t_contract_payments", "confirm_remark")

    # ── 新增字段 ──
    op.add_column(
        "t_contract_payments",
        sa.Column("reported_amount", sa.BigInteger(), nullable=False, server_default="0", comment="报送金额（用户手动填，单位：分）"),
    )
    op.add_column(
        "t_contract_payments",
        sa.Column("approved_amount", sa.BigInteger(), nullable=False, server_default="0", comment="批准金额（系统自动算，单位：分）"),
    )
    op.add_column(
        "t_contract_payments",
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", comment="状态：pending(待确认)/confirmed(已确认)/rejected(已驳回)"),
    )
    op.add_column(
        "t_contract_payments",
        sa.Column("reject_reason", sa.Text(), nullable=True, comment="驳回原因（status=rejected 时填写）"),
    )

    # ── 调整索引：删除旧 ledger_group 索引重建（列无变化但为保持一致性） ──
    # ledger_group 索引已在上一版本创建，保持不变


def downgrade() -> None:
    # ── 恢复旧字段 ──
    op.add_column(
        "t_contract_payments",
        sa.Column("payment_date", sa.Date(), nullable=False, comment="实际支付日期"),
    )
    op.add_column(
        "t_contract_payments",
        sa.Column("payment_amount", sa.BigInteger(), nullable=False, server_default="0", comment="本次支付金额（分）"),
    )
    op.add_column(
        "t_contract_payments",
        sa.Column("payer", sa.String(200), nullable=True, comment="付款方"),
    )
    op.add_column(
        "t_contract_payments",
        sa.Column("payee", sa.String(200), nullable=True, comment="收款方"),
    )
    op.add_column(
        "t_contract_payments",
        sa.Column("payment_type", sa.String(30), nullable=True, comment="支付类型"),
    )
    op.add_column(
        "t_contract_payments",
        sa.Column("confirm_status", sa.String(20), nullable=False, server_default="pending", comment="确认状态"),
    )
    op.add_column(
        "t_contract_payments",
        sa.Column("confirmed_by", UUID(as_uuid=True), nullable=True, comment="确认人用户ID"),
    )
    op.add_column(
        "t_contract_payments",
        sa.Column("confirm_remark", sa.Text(), nullable=True, comment="确认/驳回备注"),
    )

    # ── 删除新增字段 ──
    op.drop_column("t_contract_payments", "reject_reason")
    op.drop_column("t_contract_payments", "status")
    op.drop_column("t_contract_payments", "approved_amount")
    op.drop_column("t_contract_payments", "reported_amount")
