"""字典表 (V2.0 — 10 张)

所有字典表使用统一结构：(id UUID PK, code VARCHAR(50) UNIQUE, name VARCHAR(100),
sort_order INTEGER, is_active BOOLEAN, created_at TIMESTAMPTZ)

数据来源：数据字典中的枚举字段（项目性质、投资时序、形象部位等）
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import UUIDMixin, DictMixin, Base


# ── 字典基类（组合 UUID + DictMixin + created_at）──

class _BaseDict(Base, UUIDMixin, DictMixin):
    """字典表抽象基类。"""
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.code} {self.name}>"


# ── 10 张字典表 ──

class DictProjectNature(_BaseDict):
    """项目性质：功能性项目/商业性项目"""
    __tablename__ = "dict_project_nature"


class DictInvestTiming(_BaseDict):
    """投资时序：新投项目/续投项目"""
    __tablename__ = "dict_invest_timing"


class DictInvestNature(_BaseDict):
    """投资性质：固定资产投资/股权投资/其他投资"""
    __tablename__ = "dict_invest_nature"


class DictInvestStructure(_BaseDict):
    """投资结构：基础设施类/民生和社会事业类/生态环保类"""
    __tablename__ = "dict_invest_structure"


class DictInvestField(_BaseDict):
    """投资领域：装备制造/食品饮料/材料化工/生态环保/打造美丽宜居德阳"""
    __tablename__ = "dict_invest_field"


class DictProjectLevel(_BaseDict):
    """项目级别：省重点项目/市重点项目/省重点项目子项"""
    __tablename__ = "dict_project_level"


class DictLocation(_BaseDict):
    """工程部位/单体：5#平房仓/工作塔区域/油罐区/浅圆仓/围墙施工/塔吊工程/..."""
    __tablename__ = "dict_location"


class DictOwnerUnit(_BaseDict):
    """业主单位：产投集团/发展集团/商投集团/城发集团/建工集团/成德轨道/..."""
    __tablename__ = "dict_owner_unit"


class DictSupplier(_BaseDict):
    """供应商/承包单位"""
    __tablename__ = "dict_supplier"


class DictReviewType(_BaseDict):
    """审核类型：设备/设计/施工/监理过控"""
    __tablename__ = "dict_review_type"
