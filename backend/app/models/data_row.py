"""过控数据流水表 t_data_rows

系统核心数据资产表，存储所有最小颗粒度的工程数据。
金额单位统一为 分 (BIGINT)。
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin, Base


class DataRow(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_data_rows"

    # ── 关联 ──
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目",
    )

    # ── 业务字段 ──
    data_date: Mapped[date | None] = mapped_column(Date, comment="数据发生日期")
    category: Mapped[str | None] = mapped_column(String(100), index=True, comment="分部工程类别（地基/主体/装修等）")
    item_name: Mapped[str | None] = mapped_column(String(200), comment="分项名称（混凝土/钢筋/模板等）")
    planned_quantity: Mapped[int | None] = mapped_column(BigInteger, comment="计划工程量（主单位）")
    actual_quantity: Mapped[int | None] = mapped_column(BigInteger, comment="实际工程量（主单位）")
    unit: Mapped[str | None] = mapped_column(String(20), comment="单位（m³/t/m²等）")
    unit_price: Mapped[int | None] = mapped_column(BigInteger, comment="单价（分）")
    amount: Mapped[int | None] = mapped_column(BigInteger, index=True, comment="金额（分）")
    cost_type: Mapped[str | None] = mapped_column(String(50), comment="费用类型（建安工程费/二类费用）")

    # ── 来源追踪 ──
    source_doc: Mapped[str | None] = mapped_column(String(500), comment="来源文档名称")
    source_type: Mapped[str | None] = mapped_column(String(30), comment="来源：施工方上报/过控审核/AI识别/系统计算")
    raw_data: Mapped[dict | None] = mapped_column(JSONB, comment="AI 识别的原始数据快照")

    # ── 确认机制 ──
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True, comment="是否已人工确认")
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), comment="确认人")
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="确认时间")

    # ── 关系 ──
    project: Mapped["Project"] = relationship("Project", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<DataRow {self.id} item={self.item_name} confirmed={self.is_confirmed}>"
