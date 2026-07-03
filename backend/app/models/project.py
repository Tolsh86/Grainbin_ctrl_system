"""项目主表 t_projects

字段：project_name, project_code, construction_scale, total_investment,
      owner_unit, supervision_unit, design_unit, constructor_unit,
      start_date, planned_end_date, actual_end_date, project_status
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin, Base


class Project(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_projects"

    project_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="项目名称")
    project_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True, comment="项目编码")
    construction_scale: Mapped[str | None] = mapped_column(String(50), comment="建设规模（如5.2万吨）")
    total_investment: Mapped[int | None] = mapped_column(BigInteger, comment="总投资额（分）")
    owner_unit: Mapped[str | None] = mapped_column(String(200), comment="业主单位")
    supervision_unit: Mapped[str | None] = mapped_column(String(200), comment="监理单位")
    design_unit: Mapped[str | None] = mapped_column(String(200), comment="设计单位")
    constructor_unit: Mapped[str | None] = mapped_column(String(200), comment="施工单位")
    start_date: Mapped[date | None] = mapped_column(Date, comment="开工日期")
    planned_end_date: Mapped[date | None] = mapped_column(Date, comment="计划竣工日期")
    actual_end_date: Mapped[date | None] = mapped_column(Date, comment="实际竣工日期")
    project_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="前期",
        comment="状态：前期 / 施工中 / 已竣工 / 停工",
    )
    description: Mapped[str | None] = mapped_column(Text, comment="项目描述")

    def __repr__(self) -> str:
        return f"<Project {self.project_code} {self.project_name}>"
