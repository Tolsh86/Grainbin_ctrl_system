"""项目主表 t_projects (V2.0)

字段来源：数据字典 — 文件5（新投+续投）、文件6（目标计划）、文件7（省市重点项目进度）
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin, Base


class Project(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_projects"

    # ── 基本信息 ──
    project_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="项目名称"
    )
    project_code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="项目编码（业务唯一标识）"
    )

    # ── 项目分类属性 (来自文件5 新投/续投) ──
    project_nature: Mapped[str] = mapped_column(
        String(50), nullable=False, default="功能性项目", comment="项目性质：功能性项目/商业性项目"
    )
    invest_timing: Mapped[str] = mapped_column(
        String(20), nullable=False, default="续投项目", comment="投资时序：新投项目/续投项目"
    )
    invest_nature: Mapped[str | None] = mapped_column(
        String(50), comment="投资性质：固定资产投资/股权投资/其他投资"
    )
    invest_structure: Mapped[str | None] = mapped_column(
        String(50), comment="投资结构：基础设施类/民生和社会事业类/生态环保类"
    )
    invest_field: Mapped[str | None] = mapped_column(
        String(100), comment="投资领域：装备制造/食品饮料/材料化工/..."
    )
    implement_body: Mapped[str | None] = mapped_column(
        String(200), comment="实施主体（可能含换行拼接，如'产投集团\\n省食油储备'）"
    )
    implement_period: Mapped[str | None] = mapped_column(
        String(50), comment="实施时间（如'2025.12-2027.11'）"
    )
    expected_return: Mapped[str | None] = mapped_column(
        Text, comment="投资预期收益说明"
    )
    business_class: Mapped[str | None] = mapped_column(
        String(20), comment="业务划分：主业/非主业/培育业"
    )
    region: Mapped[str] = mapped_column(
        String(20), nullable=False, default="市内", comment="区域：市内/市外"
    )

    # ── 行政属性 (来自文件6) ──
    importance: Mapped[str | None] = mapped_column(
        String(10), comment="重要性：★(省重点)/▲(市重点)"
    )
    supervising_dept: Mapped[str | None] = mapped_column(
        String(200), comment="行业归口主管部门"
    )
    project_level_remark: Mapped[str | None] = mapped_column(
        String(100), comment="项目级别备注（省重点项目/子项标注）"
    )
    responsible_unit: Mapped[str | None] = mapped_column(
        String(200), comment="责任单位"
    )

    # ── 建设内容 ──
    construction_content: Mapped[str | None] = mapped_column(
        Text, comment="项目内容/建设内容（来自文件5）"
    )
    construction_scale: Mapped[str | None] = mapped_column(
        Text, comment="建设内容及规模（来自文件7）"
    )
    construction_period: Mapped[str | None] = mapped_column(
        String(50), comment="建设周期/起止年（如'600天'或'2025-2027年'）"
    )

    # ── 投资金额（单位：分，导入时万元×1,000,000）──
    planned_total_invest: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, comment="计划总投资（分）"
    )
    planned_invest_2026: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="2026年计划投资（分）"
    )

    # ── 参建单位 ──
    owner_unit: Mapped[str | None] = mapped_column(
        String(200), comment="业主单位/建设单位"
    )

    # ── 质量安全目标 (来自文件6) ──
    quality_target: Mapped[str] = mapped_column(
        String(50), nullable=False, default="合格", comment="质量目标"
    )
    safety_target: Mapped[str | None] = mapped_column(
        String(100), comment="安全目标（如'不发生一般及以上的安全事故'）"
    )

    # ── 项目状态 ──
    project_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="preparing",
        comment="状态：preparing(前期)/constructing(施工中)/completed(已竣工)/suspended(停工)",
    )

    # ── 关系 ──
    contracts: Mapped[list["Contract"]] = relationship("Contract", back_populates="project", lazy="selectin")
    progress_reviews: Mapped[list["ProgressPaymentReview"]] = relationship(
        "ProgressPaymentReview", back_populates="project", lazy="selectin"
    )
    weekly_reports: Mapped[list["WeeklyProgressReport"]] = relationship(
        "WeeklyProgressReport", back_populates="project", lazy="selectin"
    )
    weekly_metrics: Mapped[list["WeeklyProgressMetrics"]] = relationship(
        "WeeklyProgressMetrics", back_populates="project", lazy="selectin"
    )
    monthly_progress: Mapped[list["MonthlyProvinceProgress"]] = relationship(
        "MonthlyProvinceProgress", back_populates="project", lazy="selectin"
    )
    monthly_plans: Mapped[list["MonthlyTargetPlan"]] = relationship(
        "MonthlyTargetPlan", back_populates="project", lazy="selectin"
    )
    fund_breakdowns: Mapped[list["FundBreakdown"]] = relationship(
        "FundBreakdown", back_populates="project", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Project {self.project_code} {self.project_name}>"
