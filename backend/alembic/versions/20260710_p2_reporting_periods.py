"""Phase2 #1 — 创建报送期次表 t_reporting_periods

期次是审核模块的核心驱动表，一期内包含多个合同的审核数据。

Revision ID: 20260710_p2_reporting_periods
Revises: 20260710_payment_model_refactor
Create Date: 2026-07-10
"""

from typing import Union, Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "20260710_p2_reporting_periods"
down_revision: Union[str, None] = "20260710_payment_model_refactor"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "t_reporting_periods",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), comment="主键"),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"),
        sa.Column("period_no", sa.Integer(), nullable=False, comment="期次编号（1-based）"),
        sa.Column("period_month", sa.String(7), nullable=False, comment="期次月份 YYYY-MM"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft", comment="状态：draft/submitted/reviewed/closed"),
        sa.Column("remark", sa.Text(), nullable=True, comment="备注说明"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
    )
    op.create_unique_constraint("uq_period_project_no", "t_reporting_periods", ["project_id", "period_no"])
    op.create_index("ix_t_reporting_periods_status", "t_reporting_periods", ["status"])


def downgrade() -> None:
    op.drop_table("t_reporting_periods")
