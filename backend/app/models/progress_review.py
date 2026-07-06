"""进度款审核表 t_progress_payment_review (V2.0)

来源：文件2（进度款审核汇总表.xls，5 个 Sheet 中 4 个数据 Sheet）
4 类单位（设备/设计/施工/监理过控）共用单表，通过 review_type 区分。
金额单位：分（源数据为元，导入时 ×100）
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, Base


class ProgressPaymentReview(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_progress_payment_review"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"
    )
    contract_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_contracts.id"), index=True, comment="关联合同（可选）"
    )

    # ── 审核标识 ──
    review_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True, comment="审核类型：设备/设计/施工/监理过控"
    )
    period_month: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="期数/月份（如'第一期/2026年01月'）"
    )
    period_no: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="期次编号"
    )
    applicant_unit: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="申请单位"
    )

    # ── 通用金额字段 (所有 review_type 共有，单位：分) ──
    contract_amount: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, comment="合同金额（分）"
    )
    cumulative_reported_output: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, comment="累计报送产值（分）"
    )
    payment_ratio: Mapped[float | None] = mapped_column(
        Numeric(6, 4), comment="付款比例（如 0.2=20%）"
    )
    current_audited_output: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, comment="本期审核产值（分）"
    )
    cumulative_audited_output: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, comment="累计审核产值（分）"
    )
    cumulative_audited_payable: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, comment="累计审核应付款（分）"
    )

    # ── 施工类特有 (review_type='施工') ──
    constr_install_fee: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="建筑安装工程费（分）"
    )
    safety_civil_fee: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="安全文明施工费（分）"
    )
    constr_install_pay_ratio: Mapped[float | None] = mapped_column(
        Numeric(6, 4), comment="建筑安装工程费付款比例"
    )
    safety_civil_pay_ratio: Mapped[float | None] = mapped_column(
        Numeric(6, 4), comment="安全文明施工费付款比例"
    )

    # ── 监理过控类特有 (review_type='监理过控') ──
    supervision_fee: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="工程监理服务费（分）"
    )
    cost_consult_fee: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="造价咨询服务费（分）"
    )
    settlement_fee: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="竣工结算服务费（分）"
    )
    supervision_pay_ratio: Mapped[float | None] = mapped_column(
        Numeric(6, 4), comment="工程监理服务费付款比例"
    )
    cost_consult_pay_ratio: Mapped[float | None] = mapped_column(
        Numeric(6, 4), comment="造价咨询服务费付款比例"
    )
    settlement_pay_ratio: Mapped[float | None] = mapped_column(
        Numeric(6, 4), comment="竣工结算服务费付款比例"
    )

    # ── 审核类型特有动态字段 (V2.2 新增) ──
    extra_fields: Mapped[dict | None] = mapped_column(
        JSONB, comment="审核类型特有的动态字段。施工审核示例: {\"建安工程费\": xxx, \"安全文明费\": xxx}；未来检测审核无需改表结构"
    )

    # ── 备注 ──
    remark: Mapped[str | None] = mapped_column(
        Text, comment="备注（含税说明、分账说明等）"
    )
    tax_rate: Mapped[float | None] = mapped_column(
        Numeric(4, 2), comment="税率（如 9.00=9%, 6.00=6%）"
    )

    # ── 审核状态 ──
    audit_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        comment="审核状态：pending(待审)/auditing(审核中)/audited(已审)/paid(已付)"
    )
    submit_date: Mapped[date | None] = mapped_column(
        Date, comment="申报日期"
    )
    audited_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_users.id"), comment="审核人"
    )
    audited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="审核时间"
    )

    # ── 关系 ──
    project: Mapped["Project"] = relationship("Project", back_populates="progress_reviews", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ProgressReview {self.review_type} period={self.period_no}>"
