"""支付节点模板表 t_node_templates (V2.2)

用户可通过模板一键生成合同的支付节点，支持预置模板和自定义模板。

预置模板（基于川西项目真实数据）:
- 监理合同标准节点 (supervision) — 6 节点，来源于 CX009 中凯俊成
- 设计合同标准节点 (design) — 5 节点，来源于 CX005 中储粮研究院
- 检测合同标准节点 (testing) — 3 节点，来源于 CX016 检测合同
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin, Base


class NodeTemplate(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_node_templates"

    template_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="模板名称（如'监理合同标准节点'）"
    )
    biz_type: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True,
        comment="业务类型: supervision/design/testing/construction/custom"
    )
    description: Mapped[str | None] = mapped_column(
        Text, comment="模板描述"
    )
    is_preset: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="True=系统预置, False=用户自定义"
    )
    stages: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=list,
        comment=(
            "节点配置数组 JSON: "
            '[{"order":1,"node_name":"合同签订","agreed_ratio":0.10,"trigger_condition":"签订后7日内","offset_days":7}, ...]'
        )
    )

    def __repr__(self) -> str:
        return f"<NodeTemplate {self.template_name} type={self.biz_type}>"
