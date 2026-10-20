"""V2.3 — implement_period(VARCHAR) → start_date(DATE) + end_date(DATE)

现有数据：
- 种子项目 implement_period 有值（如 '2025.12-2027.11'）→ 解析回填
- test1/test2 为 NULL → 保持 NULL（付款矩阵有容错逻辑）

变更：
1. 新增 start_date (DATE, nullable) + end_date (DATE, nullable)
2. 从现有 implement_period 回填
3. 删除 implement_period 列

Revision ID: 20260709_period_to_dates
Revises: 20260709_backfill_agreed_amount
Create Date: 2026-07-09
"""

from typing import Union, Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260709_period_to_dates"
down_revision: Union[str, None] = "20260709_backfill_agreed_amount"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 新增 start_date + end_date（允许为空）
    op.add_column(
        "t_projects",
        sa.Column("start_date", sa.Date(), nullable=True, comment="实施起始月"),
    )
    op.add_column(
        "t_projects",
        sa.Column("end_date", sa.Date(), nullable=True, comment="实施结束月"),
    )

    # 2. 从 implement_period 回填（格式：2025.12-2027.11 → start=2025-12-01, end=2027-11-01）
    # 使用 POSIX 兼容的 [0-9] 而非 \d
    op.execute(
        """
        UPDATE t_projects
        SET
            start_date = (regexp_replace(implement_period, '^([0-9]{4})\\.([0-9]{1,2})-.*$', '\\1-\\2-01'))::date,
            end_date   = (regexp_replace(implement_period, '^.*-([0-9]{4})\\.([0-9]{1,2})$', '\\1-\\2-01'))::date
        WHERE implement_period ~ '^[0-9]{4}\\.[0-9]{1,2}-[0-9]{4}\\.[0-9]{1,2}$'
        """
    )

    # 3. 删除旧的 implement_period 列
    op.drop_column("t_projects", "implement_period")


def downgrade() -> None:
    # 1. 恢复 implement_period 列
    op.add_column(
        "t_projects",
        sa.Column("implement_period", sa.String(50), nullable=True, comment="实施时间"),
    )

    # 2. 从 start_date/end_date 转回 implement_period 字符串
    op.execute(
        """
        UPDATE t_projects
        SET implement_period = TO_CHAR(start_date, 'YYYY.MM') || '-' || TO_CHAR(end_date, 'YYYY.MM')
        WHERE start_date IS NOT NULL AND end_date IS NOT NULL
        """
    )

    # 3. 删除 start_date + end_date
    op.drop_column("t_projects", "end_date")
    op.drop_column("t_projects", "start_date")
