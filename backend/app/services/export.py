"""审核汇总表 Excel 导出服务 (Phase2)

复刻真实汇总表格式：
- Sheet 1：封面（项目信息 + 承包单位列表 + 期数 + 月份）
- Sheet 2：建安费用汇总（review_mode=daily_aggregate 的合同审定值汇总）
- Sheet 3-N：按供应商分表（每张含费用分项明细）
"""

from __future__ import annotations

import io
import uuid
from datetime import date

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.reporting_period import ReportingPeriod
from app.models.progress_review import ProgressPaymentReview
from app.models.contract import Contract
from app.models.project import Project
from app.core.exceptions import NotFound
from app.utils.db import fen_to_wan_yuan


def _wan(fen: int | None) -> float:
    """分→万元，保留 4 位小数。None/0 返回 0.0。"""
    if not fen:
        return 0.0
    return round(fen_to_wan_yuan(fen), 4)


# ═══════════════════════════════════════════════════════════════════
# 数据获取
# ═══════════════════════════════════════════════════════════════════


async def _get_period_export_data(db: AsyncSession, period_id: uuid.UUID) -> dict:
    """获取期次导出所需的全部数据。

    Returns:
        {period, project, reviews: [{review, contract, fee_items}]}
    """
    # 期次 + 项目
    period = await db.get(ReportingPeriod, period_id)
    if not period:
        raise NotFound(detail="期次不存在")

    project = await db.get(Project, period.project_id)
    if not project:
        raise NotFound(detail="关联项目不存在")

    # 审核记录 + 费用分项 + 合同
    result = await db.execute(
        select(ProgressPaymentReview)
        .options(
            selectinload(ProgressPaymentReview.fee_items),
            selectinload(ProgressPaymentReview.contract),
        )
        .where(ProgressPaymentReview.period_id == period_id)
        .order_by(ProgressPaymentReview.review_type, ProgressPaymentReview.applicant_unit)
    )
    reviews = list(result.scalars().all())

    return {
        "period": period,
        "project": project,
        "reviews": reviews,
    }


# ═══════════════════════════════════════════════════════════════════
# Excel 构建
# ═══════════════════════════════════════════════════════════════════


def build_period_export_excel(data: dict) -> io.BytesIO:
    """根据期次数据构建多 Sheet 审核汇总表 Excel。

    Sheet 结构：
    1. 封面 — 项目信息 + 承包单位概览
    2. 建安费用汇总 — daily_aggregate 合同汇总
    3+. 供应商分表 — 每个合同一张，含费用分项明细
    """
    from openpyxl import Workbook
    from openpyxl.styles import (
        Alignment, Border, Font, PatternFill, Side,
    )
    from openpyxl.utils import get_column_letter

    period = data["period"]
    project = data["project"]
    reviews: list[ProgressPaymentReview] = data["reviews"]

    wb = Workbook()

    # ── 样式常量 ──
    cover_title_font = Font(name="微软雅黑", size=18, bold=True)
    cover_subtitle_font = Font(name="微软雅黑", size=12, bold=True)
    cover_label_font = Font(name="微软雅黑", size=11, bold=True)
    cover_value_font = Font(name="微软雅黑", size=11)
    header_font = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    data_font = Font(name="微软雅黑", size=10)
    bold_font = Font(name="微软雅黑", size=10, bold=True)
    total_fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)
    right_align = Alignment(horizontal="right", vertical="center")

    # ═══════════════════════════════════════════════════════════════
    # Sheet 1: 封面
    # ═══════════════════════════════════════════════════════════════
    ws_cover = wb.active
    ws_cover.title = "封面"

    # 列宽
    for ci, w in enumerate([16, 30, 20, 16, 20], 1):
        ws_cover.column_dimensions[get_column_letter(ci)].width = w

    row = 1

    # 大标题
    ws_cover.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    c = ws_cover.cell(row=row, column=1, value="兴天华过控智能平台")
    c.font = Font(name="微软雅黑", size=20, bold=True)
    c.alignment = center_align
    row += 1

    ws_cover.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    c = ws_cover.cell(row=row, column=1, value="进度产值审核汇总表")
    c.font = cover_title_font
    c.alignment = center_align
    row += 2

    # 项目基本信息
    info_rows = [
        ("项目名称", project.project_name or ""),
        ("项目编号", project.project_code or ""),
        ("报送期次", f"第 {period.period_no} 期"),
        ("报送月份", period.period_month),
        ("审核状态", _status_text(period.status)),
        ("编制日期", date.today().isoformat()),
    ]
    for label, value in info_rows:
        ws_cover.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
        cl = ws_cover.cell(row=row, column=1, value=f"{label}：")
        cl.font = cover_label_font
        cl.alignment = left_align
        ws_cover.merge_cells(start_row=row, start_column=3, end_row=row, end_column=5)
        cv = ws_cover.cell(row=row, column=3, value=value)
        cv.font = cover_value_font
        cv.alignment = left_align
        row += 1

    row += 1

    # 承包单位概览
    ws_cover.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    c = ws_cover.cell(row=row, column=1, value="承包单位概览")
    c.font = cover_subtitle_font
    c.alignment = left_align
    row += 1

    # 概览表头
    cover_headers = ["序号", "申报单位", "合同编号", "合同金额(万元)", "审核类型"]
    for ci, h in enumerate(cover_headers, 1):
        cell = ws_cover.cell(row=row, column=ci, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    row += 1

    for i, rv in enumerate(reviews):
        ctr = rv.contract
        row_data = [
            i + 1,
            rv.applicant_unit,
            ctr.contract_no if ctr else "—",
            _wan(ctr.contract_amount) if ctr else 0.0,
            rv.review_type,
        ]
        for ci, val in enumerate(row_data, 1):
            cell = ws_cover.cell(row=row, column=ci, value=val)
            cell.font = data_font
            cell.alignment = center_align if ci in (1, 5) else left_align
            cell.border = thin_border
            if ci == 4 and isinstance(val, (int, float)):
                cell.alignment = right_align
                cell.number_format = "#,##0.0000"
        row += 1

    # ═══════════════════════════════════════════════════════════════
    # Sheet 2: 建安费用汇总
    # ═══════════════════════════════════════════════════════════════
    _write_summary_sheet(
        wb, "建安费用汇总", reviews, period, "daily_aggregate",
        header_font, header_fill, data_font, bold_font, total_fill,
        thin_border, center_align, left_align, right_align,
    )

    # ═══════════════════════════════════════════════════════════════
    # Sheet 3+: 二类费用供应商分表（node_judge 合同，每个一张）
    # ═══════════════════════════════════════════════════════════════
    for rv in reviews:
        mode = "daily_aggregate"
        if rv.contract:
            mode = rv.contract.review_mode or "node_judge"
        # 按 review_mode 分流：daily_aggregate 进汇总 sheet；node_judge 每合同独立 sheet
        if mode == "daily_aggregate":
            continue

        ctr = rv.contract
        sheet_name = _safe_sheet_name(rv.applicant_unit)
        _write_supplier_sheet(
            wb, sheet_name, rv, period,
            header_font, header_fill, data_font, bold_font, total_fill,
            thin_border, center_align, left_align, right_align,
        )

    # 如果没有 node_judge 合同，加一个空说明 sheet
    if not any(
        rv.contract and rv.contract.review_mode != "daily_aggregate"
        for rv in reviews
    ):
        ws_empty = wb.create_sheet("二类费用（无数据）")
        ws_empty.cell(row=2, column=2, value="本期次无二类费用合同审核数据")

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ═══════════════════════════════════════════════════════════════════
# Sheet 构建函数
# ═══════════════════════════════════════════════════════════════════


def _write_summary_sheet(
    wb, sheet_name: str,
    reviews: list[ProgressPaymentReview],
    period,
    target_mode: str,
    header_font, header_fill, data_font, bold_font, total_fill,
    thin_border, center_align, left_align, right_align,
):
    """写入建安费用汇总 Sheet。"""
    from openpyxl.utils import get_column_letter

    ws = wb.create_sheet(title=sheet_name)

    filtered = [
        rv for rv in reviews
        if rv.contract and rv.contract.review_mode == target_mode
    ]

    HEADERS = [
        "序号", "申报单位", "合同编号", "合同金额\n(万元)",
        "累计报送产值\n(万元)", "本期审定产值\n(万元)",
        "累计审定产值\n(万元)", "累计应付款\n(万元)",
        "费用分项明细", "备注",
    ]
    COL_WIDTHS = [6, 20, 14, 14, 14, 14, 14, 14, 50, 20]

    for ci, w in enumerate(COL_WIDTHS, 1):
        ws.column_dimensions[get_column_letter(ci)].width = w

    row = 1

    # 标题
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=len(HEADERS))
    title_cell = ws.cell(
        row=row, column=1,
        value=f"建安费用审核汇总 — 第 {period.period_no} 期（{period.period_month}）"
    )
    title_cell.font = Font(name="微软雅黑", size=14, bold=True)
    title_cell.alignment = center_align
    row += 2

    # 表头
    for ci, h in enumerate(HEADERS, 1):
        cell = ws.cell(row=row, column=ci, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    row += 1

    if not filtered:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=len(HEADERS))
        ws.cell(row=row, column=1, value="本期末参与建安费用审核的合同").font = data_font
        return

    _write_review_rows(
        ws, row, filtered, HEADERS,
        data_font, bold_font, total_fill,
        thin_border, center_align, left_align, right_align,
    )


def _write_supplier_sheet(
    wb, sheet_name: str,
    review: ProgressPaymentReview,
    period,
    header_font, header_fill, data_font, bold_font, total_fill,
    thin_border, center_align, left_align, right_align,
):
    """写入单个供应商（二类费用合同）的审核分表。"""
    from openpyxl.utils import get_column_letter

    ws = wb.create_sheet(title=sheet_name)
    ctr = review.contract

    row = 1

    # 标题
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=8)
    title = ws.cell(
        row=row, column=1,
        value=f"{review.applicant_unit} — 进度产值审核表"
    )
    title.font = Font(name="微软雅黑", size=14, bold=True)
    title.alignment = center_align
    row += 1

    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=8)
    ws.cell(row=row, column=1, value=f"第 {period.period_no} 期 · {period.period_month}").font = Font(name="微软雅黑", size=11)
    row += 1

    # 基本信息
    info = [
        ("合同编号", ctr.contract_no if ctr else "—"),
        ("申报单位", review.applicant_unit),
        ("合同金额(万元)", f"{_wan(ctr.contract_amount) if ctr else 0:.4f}"),
        ("审核类型", review.review_type),
        ("审核状态", _status_text(review.audit_status)),
    ]
    for label, val in info:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
        ws.cell(row=row, column=1, value=f"{label}：").font = bold_font
        ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=4)
        ws.cell(row=row, column=3, value=str(val)).font = data_font
        row += 1

    row += 1

    # 费用分项明细表头
    HEADERS = [
        "序号", "费用分项", "付款比例",
        "报送金额\n(万元)", "审定金额\n(万元)",
        "应付金额\n(万元)", "备注",
    ]
    COL_WIDTHS = [6, 24, 12, 14, 14, 14, 20]

    for ci, w in enumerate(COL_WIDTHS, 1):
        ws.column_dimensions[get_column_letter(ci)].width = w

    for ci, h in enumerate(HEADERS, 1):
        cell = ws.cell(row=row, column=ci, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    row += 1

    fee_items = review.fee_items or []
    total_reported = 0
    total_reviewed = 0
    total_payable = 0

    for i, fi in enumerate(fee_items):
        reported = fi.reported_amount or 0
        reviewed = fi.reviewed_amount or 0
        ratio = fi.payment_ratio or 0
        payable = int(reviewed * ratio)

        total_reported += reported
        total_reviewed += reviewed
        total_payable += payable

        row_data = [
            i + 1,
            fi.item_name,
            f"{ratio * 100:.2f}%" if ratio else "—",
            _wan(reported),
            _wan(reviewed),
            _wan(payable),
            fi.remark or "",
        ]
        for ci, val in enumerate(row_data, 1):
            cell = ws.cell(row=row, column=ci, value=val)
            cell.font = data_font
            cell.border = thin_border
            if ci in (1, 3):
                cell.alignment = center_align
            elif ci == 7:
                cell.alignment = left_align
            else:
                cell.alignment = right_align
                if isinstance(val, (int, float)) and ci >= 4:
                    cell.number_format = "#,##0.0000"
        row += 1

    # 合计行
    subtotal = ["", "合计", "", _wan(total_reported), _wan(total_reviewed), _wan(total_payable), ""]
    for ci, val in enumerate(subtotal, 1):
        cell = ws.cell(row=row, column=ci, value=val)
        cell.font = bold_font
        cell.fill = total_fill
        cell.border = thin_border
        if ci == 2:
            cell.alignment = right_align
        elif ci >= 3 and val != "":
            cell.alignment = right_align
            if isinstance(val, (int, float)):
                cell.number_format = "#,##0.0000"
        else:
            cell.alignment = center_align

    row += 2

    # 底部汇总信息
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    ws.cell(row=row, column=1, value="累计报送产值(万元)：").font = bold_font
    ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=5)
    ws.cell(row=row, column=4, value=_wan(review.cumulative_reported_output)).font = data_font
    ws.cell(row=row, column=4).alignment = right_align
    ws.cell(row=row, column=4).number_format = "#,##0.0000"
    row += 1

    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    ws.cell(row=row, column=1, value="累计审定产值(万元)：").font = bold_font
    ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=5)
    ws.cell(row=row, column=4, value=_wan(review.cumulative_audited_output)).font = data_font
    ws.cell(row=row, column=4).alignment = right_align
    ws.cell(row=row, column=4).number_format = "#,##0.0000"
    row += 1

    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    ws.cell(row=row, column=1, value="累计应付款(万元)：").font = bold_font
    ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=5)
    ws.cell(row=row, column=4, value=_wan(review.cumulative_audited_payable)).font = data_font
    ws.cell(row=row, column=4).alignment = right_align
    ws.cell(row=row, column=4).number_format = "#,##0.0000"


def _write_review_rows(
    ws, row: int,
    reviews: list[ProgressPaymentReview],
    HEADERS: list[str],
    data_font, bold_font, total_fill,
    thin_border, center_align, left_align, right_align,
) -> int:
    """写入审核数据行 + 合计行，返回下一可用行号。"""
    total_reported = 0
    total_current_output = 0
    total_cum_output = 0
    total_payable = 0

    for i, rv in enumerate(reviews):
        ctr = rv.contract
        fee_text = _format_fee_items(rv.fee_items)

        total_reported += rv.cumulative_reported_output or 0
        total_current_output += rv.current_audited_output or 0
        total_cum_output += rv.cumulative_audited_output or 0
        total_payable += rv.cumulative_audited_payable or 0

        row_data = [
            i + 1,
            rv.applicant_unit,
            ctr.contract_no if ctr else "—",
            _wan(ctr.contract_amount) if ctr else 0.0,
            _wan(rv.cumulative_reported_output),
            _wan(rv.current_audited_output),
            _wan(rv.cumulative_audited_output),
            _wan(rv.cumulative_audited_payable),
            fee_text,
            rv.remark or "",
        ]
        for ci, val in enumerate(row_data, 1):
            cell = ws.cell(row=row, column=ci, value=val)
            cell.font = data_font
            cell.border = thin_border
            if ci == 1:
                cell.alignment = center_align
            elif ci in (4, 5, 6, 7, 8):
                cell.alignment = right_align
                if isinstance(val, (int, float)):
                    cell.number_format = "#,##0.0000"
            elif ci == 9:
                cell.alignment = left_align
            else:
                cell.alignment = left_align
        row += 1

    # 合计行
    subtotal = [
        "", "合计", "",
        "",  # 合同金额不汇总
        _wan(total_reported),
        _wan(total_current_output),
        _wan(total_cum_output),
        _wan(total_payable),
        "", "",
    ]
    for ci, val in enumerate(subtotal, 1):
        cell = ws.cell(row=row, column=ci, value=val)
        cell.font = bold_font
        cell.fill = total_fill
        cell.border = thin_border
        if ci == 2:
            cell.alignment = center_align
        elif ci >= 4 and val != "":
            cell.alignment = right_align
            if isinstance(val, (int, float)):
                cell.number_format = "#,##0.0000"
        else:
            cell.alignment = center_align
    row += 1

    return row


# ═══════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════


def _format_fee_items(fee_items: list) -> str:
    """将费用分项列表格式化为展示文本。"""
    if not fee_items:
        return ""
    parts = []
    for fi in fee_items:
        ratio = fi.payment_ratio
        ratio_str = f"{(ratio or 0) * 100:.1f}%" if ratio else "—"
        parts.append(
            f"{fi.item_name}（{ratio_str}）: "
            f"报{_wan(fi.reported_amount):.4f}/"
            f"审{_wan(fi.reviewed_amount):.4f}"
        )
    return " | ".join(parts)


def _safe_sheet_name(name: str) -> str:
    """将供应商名称转为合法的 Excel Sheet 名（≤ 31 字符）。"""
    # 替换非法字符
    safe = name.replace(":", "").replace("\\", "").replace("/", "").replace("?", "")
    safe = safe.replace("*", "").replace("[", "").replace("]", "")
    if len(safe) > 31:
        safe = safe[:28] + "..."
    return safe or "未命名"


def _status_text(s: str) -> str:
    mapping = {
        "draft": "草稿",
        "in_progress": "进行中",
        "submitted": "已报送",
        "reviewed": "已审定",
        "closed": "已关闭",
    }
    return mapping.get(s, s)
