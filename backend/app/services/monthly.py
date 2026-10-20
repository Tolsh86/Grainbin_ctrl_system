"""月度台账服务

提供：
- upsert_monthly_detail: 按合同+月份 upsert 月度台账，source=manual 防覆盖
- get_project_monthly_summary: 按项目+月份、contract_group 分组汇总产值/应付/完成比例

约定：所有金额单位为"分"（BIGINT），展示层转换使用 app.utils.db 中的金额工具函数。
"""

from __future__ import annotations

import io
import uuid
from datetime import date

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFound, BadRequest
from app.models.contract import Contract, ContractMonthlyDetail
from app.utils.db import fen_to_wan_yuan


async def upsert_monthly_detail(
    db: AsyncSession,
    *,
    contract_id: uuid.UUID,
    detail_month: date,
    payment_amount: int = 0,
    output_amount: int = 0,
    est_cumulative_payable: int = 0,
    actual_cumulative_paid: int = 0,
    est_remaining_unpaid: int = 0,
    cumulative_completed: int = 0,
    remaining_uncompleted: int = 0,
    completed_ratio: float | None = None,
    remaining_ratio: float | None = None,
    cost_items_detail: dict | None = None,
    status: str = "pending",
) -> ContractMonthlyDetail | None:
    """按合同+月份 upsert 月度台账明细（事务内完成 flush）。

    写入策略：
    - 已有 source="manual" 的记录 → 跳过，返回 None（人工审定数据不被自动汇总覆盖）
    - 已有 source="auto" 的记录 → 更新全部字段
    - 无记录 → 创建，source="auto"

    Args:
        db: 异步数据库会话
        contract_id: 合同 ID
        detail_month: 明细月份（如 ``date(2026, 1, 1)``）
        payment_amount: 当月支付金额（分）
        output_amount: 当月产值（分）
        est_cumulative_payable: 预估累计应支付（分）
        actual_cumulative_paid: 实际累计已支付（分）
        est_remaining_unpaid: 预估剩余未支付（分）
        cumulative_completed: 累计已完成产值（分）
        remaining_uncompleted: 剩余未完成产值（分）
        completed_ratio: 已完比例（0~1）
        remaining_ratio: 剩余未完比例（0~1）
        cost_items_detail: 分项级产值明细
            ``{"items": [{"fee_item_id", "name", "output", "ratio", "payable"}]}``
        status: 确认状态（pending/confirmed）

    Returns:
        创建/更新后的 ContractMonthlyDetail；被 manual 记录阻止时返回 None

    Raises:
        NotFound: 合同不存在
    """
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id, Contract.deleted_at.is_(None))
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise NotFound(detail=f"合同不存在: {contract_id}")

    result = await db.execute(
        select(ContractMonthlyDetail).where(
            ContractMonthlyDetail.contract_no == contract.contract_no,
            ContractMonthlyDetail.detail_month == detail_month,
        )
    )
    existing = result.scalar_one_or_none()

    if existing and existing.source == "manual":
        logger.info(
            f"月度明细已有人工审定数据，跳过自动汇总: "
            f"contract={contract.contract_no}, month={detail_month}"
        )
        return None

    if existing:
        existing.payment_amount = payment_amount
        existing.output_amount = output_amount
        existing.est_cumulative_payable = est_cumulative_payable
        existing.actual_cumulative_paid = actual_cumulative_paid
        existing.est_remaining_unpaid = est_remaining_unpaid
        existing.cumulative_completed = cumulative_completed
        existing.remaining_uncompleted = remaining_uncompleted
        existing.completed_ratio = completed_ratio
        existing.remaining_ratio = remaining_ratio
        existing.cost_items_detail = cost_items_detail
        existing.status = status
        existing.source = "auto"
        await db.flush()
        await db.refresh(existing)
        logger.info(
            f"月度明细已更新: contract={contract.contract_no}, month={detail_month}"
        )
        return existing

    detail = ContractMonthlyDetail(
        contract_id=contract_id,
        contract_no=contract.contract_no,
        detail_month=detail_month,
        payment_amount=payment_amount,
        output_amount=output_amount,
        est_cumulative_payable=est_cumulative_payable,
        actual_cumulative_paid=actual_cumulative_paid,
        est_remaining_unpaid=est_remaining_unpaid,
        cumulative_completed=cumulative_completed,
        remaining_uncompleted=remaining_uncompleted,
        completed_ratio=completed_ratio,
        remaining_ratio=remaining_ratio,
        source="auto",
        status=status,
        cost_items_detail=cost_items_detail,
    )
    db.add(detail)
    await db.flush()
    await db.refresh(detail)
    logger.info(
        f"月度明细已创建: contract={contract.contract_no}, month={detail_month}"
    )
    return detail


async def get_project_monthly_summary(
    db: AsyncSession,
    project_id: uuid.UUID,
    month: date | None = None,
) -> list[dict]:
    """按项目+月份、contract_group 分组汇总所有分项产值、应付金额、完成比例。

    查询项目下所有合同的月度明细，按 ``(contract_group, detail_month)`` 分组聚合：

    - total_output / total_payable: 组内产值与应付合计（分）
    - completed_ratio: 按 output_amount 加权的平均完成比例
    - fee_items: cost_items_detail 中各分项按 fee_item_id 汇总后展开为列表
    - contract_count / detail_count: 组内合同数与明细条数

    Args:
        db: 异步数据库会话
        project_id: 项目 ID
        month: 筛选月份；为 None 时返回所有月份

    Returns:
        ``[{contract_group, month, total_output, total_payable,
           completed_ratio, fee_items, contract_count, detail_count}, ...]``
        按 month desc, contract_group 排序
    """
    contracts_result = await db.execute(
        select(Contract).where(
            Contract.project_id == project_id,
            Contract.deleted_at.is_(None),
        )
    )
    contracts = list(contracts_result.scalars().all())
    if not contracts:
        return []

    contract_nos = [c.contract_no for c in contracts]
    contract_map = {c.contract_no: c for c in contracts}

    stmt = select(ContractMonthlyDetail).where(
        ContractMonthlyDetail.contract_no.in_(contract_nos)
    )
    if month:
        stmt = stmt.where(ContractMonthlyDetail.detail_month == month)

    details_result = await db.execute(stmt)
    details = list(details_result.scalars().all())

    # ── 按 (contract_group, detail_month) 分组汇总 ──
    groups: dict[tuple[str, date], dict] = {}

    for d in details:
        c = contract_map.get(d.contract_no)
        if not c:
            continue

        group_key = (c.contract_group or "__ungrouped__", d.detail_month)

        if group_key not in groups:
            groups[group_key] = {
                "contract_group": c.contract_group or "__ungrouped__",
                "month": d.detail_month,
                "total_output": 0,
                "total_payable": 0,
                "weighted_ratio_sum": 0.0,
                "ratio_weight": 0,
                "fee_items": {},  # str(fee_item_id) → {fee_item_id, name, output, payable}
                "contract_nos": set(),
                "detail_count": 0,
            }

        g = groups[group_key]
        g["total_output"] += d.output_amount or 0
        g["total_payable"] += d.payment_amount or 0
        g["contract_nos"].add(d.contract_no)
        g["detail_count"] += 1

        # 加权完成比例
        if d.completed_ratio is not None and (d.output_amount or 0) > 0:
            g["weighted_ratio_sum"] += float(d.completed_ratio) * (d.output_amount or 0)
            g["ratio_weight"] += d.output_amount or 0

        # 展开 cost_items_detail 中的分项
        if d.cost_items_detail and isinstance(d.cost_items_detail, dict):
            items = d.cost_items_detail.get("items", [])
            if isinstance(items, list):
                for item in items:
                    fid = item.get("fee_item_id") if isinstance(item, dict) else None
                    if fid is None:
                        continue
                    fid_str = str(fid)
                    if fid_str not in g["fee_items"]:
                        g["fee_items"][fid_str] = {
                            "fee_item_id": fid,
                            "name": item.get("name", ""),
                            "output": 0,
                            "payable": 0,
                        }
                    g["fee_items"][fid_str]["output"] += item.get("output", 0) or 0
                    g["fee_items"][fid_str]["payable"] += item.get("payable", 0) or 0

    # ── 构造返回结果 ──
    result: list[dict] = []
    for (group_name, month_val), g in groups.items():
        ratio = (
            round(g["weighted_ratio_sum"] / g["ratio_weight"], 4)
            if g["ratio_weight"] > 0
            else 0.0
        )
        result.append({
            "contract_group": group_name,
            "month": month_val.isoformat() if month_val else None,
            "total_output": g["total_output"],
            "total_payable": g["total_payable"],
            "completed_ratio": ratio,
            "fee_items": list(g["fee_items"].values()),
            "contract_count": len(g["contract_nos"]),
            "detail_count": g["detail_count"],
        })

    result.sort(key=lambda r: (r["month"] or "", r["contract_group"]))
    return result


# ═══════════════════════════════════════════════════════════════════
# 台账列表查询
# ═══════════════════════════════════════════════════════════════════

async def get_project_monthly_list(
    db: AsyncSession,
    project_id: uuid.UUID,
    month: date | None = None,
) -> dict:
    """按月份分组查询项目月度台账列表。

    返回每合同当月的 | 本月产值 | 本月应付 | 累计产值 | 累计应付 | 完成率 | fee_items。
    cumulative 为该项目合同下所有月份的总和。
    """
    contracts_result = await db.execute(
        select(Contract).where(
            Contract.project_id == project_id,
            Contract.deleted_at.is_(None),
        )
    )
    contracts = list(contracts_result.scalars().all())
    if not contracts:
        return {"project_id": str(project_id), "groups": []}

    contract_nos = [c.contract_no for c in contracts]
    contract_map = {c.contract_no: c for c in contracts}

    # 查指定月的月度明细
    month_detail_stmt = select(ContractMonthlyDetail).where(
        ContractMonthlyDetail.contract_no.in_(contract_nos)
    )
    if month:
        month_detail_stmt = month_detail_stmt.where(ContractMonthlyDetail.detail_month == month)
    details_result = await db.execute(month_detail_stmt)
    details = list(details_result.scalars().all())

    # 查所有累计：每个合同号各月的 output_amount 之和
    cumulative_result = await db.execute(
        select(
            ContractMonthlyDetail.contract_no,
            func.coalesce(func.sum(ContractMonthlyDetail.output_amount), 0).label("cumulative_output"),
            func.coalesce(func.sum(ContractMonthlyDetail.payment_amount), 0).label("cumulative_payable"),
        )
        .where(ContractMonthlyDetail.contract_no.in_(contract_nos))
        .group_by(ContractMonthlyDetail.contract_no)
    )
    cumulative_map = {r[0]: (r[1], r[2]) for r in cumulative_result.all()}

    # ── 按 detail_month 分组 ──
    month_groups: dict[date, list[ContractMonthlyDetail]] = {}
    for d in details:
        month_groups.setdefault(d.detail_month, []).append(d)

    # ── 构造响应 ──
    groups: list[dict] = []
    for dm in sorted(month_groups.keys()):
        group_contracts: list[dict] = []
        group_monthly_output = 0
        group_monthly_payable = 0
        group_cumulative_output = 0
        group_cumulative_payable = 0

        for d in month_groups[dm]:
            c = contract_map.get(d.contract_no)
            if not c:
                continue

            cum_out, cum_pay = cumulative_map.get(d.contract_no, (0, 0))

            fee_items: list[dict] = []
            if d.cost_items_detail and isinstance(d.cost_items_detail, dict):
                items = d.cost_items_detail.get("items", [])
                if isinstance(items, list):
                    for fi in items:
                        if isinstance(fi, dict):
                            fee_items.append({
                                "fee_item_id": str(fi.get("fee_item_id", "")),
                                "name": fi.get("name", ""),
                                "output": fi.get("output", 0) or 0,
                                "payable": fi.get("payable", 0) or 0,
                            })

            group_contracts.append({
                "detail_id": d.id,
                "contract_id": c.id,
                "contract_no": c.contract_no,
                "supplier_name": c.supplier_name,
                "review_mode": c.review_mode,
                "ledger_group": c.ledger_group,
                "contract_group": c.contract_group,
                "contract_amount": c.contract_amount,
                "monthly_output": d.output_amount or 0,
                "monthly_payable": d.payment_amount or 0,
                "cumulative_output": cum_out or 0,
                "cumulative_payable": cum_pay or 0,
                "completed_ratio": d.completed_ratio,
                "fee_items": fee_items,
                "source": d.source,
                "status": d.status,
            })
            group_monthly_output += d.output_amount or 0
            group_monthly_payable += d.payment_amount or 0
            group_cumulative_output += cum_out or 0
            group_cumulative_payable += cum_pay or 0

        groups.append({
            "month": dm.isoformat(),
            "contracts": group_contracts,
            "group_monthly_output": group_monthly_output,
            "group_monthly_payable": group_monthly_payable,
            "group_cumulative_output": group_cumulative_output,
            "group_cumulative_payable": group_cumulative_payable,
        })

    return {"project_id": str(project_id), "groups": groups}


# ═══════════════════════════════════════════════════════════════════
# 手动更新台账
# ═══════════════════════════════════════════════════════════════════

async def manual_upsert_monthly_detail(
    db: AsyncSession,
    contract_id: uuid.UUID,
    data: dict,
) -> ContractMonthlyDetail:
    """手动更新/创建月度台账明细，source 固定为 manual。

    - 已有 manual 记录 → 更新字段
    - 已有 auto 记录 → 覆写为 manual（人工审定覆盖系统汇总）
    - 无记录 → 新建 manual
    """
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id, Contract.deleted_at.is_(None))
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise NotFound(detail=f"合同不存在: {contract_id}")

    detail_month = data["detail_month"]

    result = await db.execute(
        select(ContractMonthlyDetail).where(
            ContractMonthlyDetail.contract_no == contract.contract_no,
            ContractMonthlyDetail.detail_month == detail_month,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        for key, value in data.items():
            if key != "detail_month" and value is not None:
                setattr(existing, key, value)
        existing.source = "manual"
        existing.contract_id = contract_id
        await db.flush()
        await db.refresh(existing)
        logger.info(f"月度明细手动更新: contract={contract.contract_no}, month={detail_month}")
        return existing

    detail = ContractMonthlyDetail(
        contract_id=contract_id,
        contract_no=contract.contract_no,
        detail_month=detail_month,
        source="manual",
        **{k: v for k, v in data.items() if k != "detail_month" and v is not None},
    )
    db.add(detail)
    await db.flush()
    await db.refresh(detail)
    logger.info(f"月度明细手动创建(manual): contract={contract.contract_no}, month={detail_month}")
    return detail


# ═══════════════════════════════════════════════════════════════════
# 撤回确认
# ═══════════════════════════════════════════════════════════════════

async def revoke_monthly_detail(
    db: AsyncSession,
    detail_id: uuid.UUID,
) -> ContractMonthlyDetail:
    """撤回月度台账确认：仅 source=manual 且 status=confirmed 允许撤回 → pending。"""
    result = await db.execute(
        select(ContractMonthlyDetail).where(ContractMonthlyDetail.id == detail_id)
    )
    detail = result.scalar_one_or_none()
    if not detail:
        raise NotFound(detail="月度明细不存在")

    if detail.source != "manual":
        raise BadRequest(detail="仅人工审定(source=manual)的台账允许撤回")
    if detail.status != "confirmed":
        raise BadRequest(detail=f"当前状态 '{detail.status}' 不允许撤回，仅 confirmed 可撤回")

    detail.status = "pending"
    await db.flush()
    await db.refresh(detail)
    logger.info(f"月度明细撤回: id={detail_id}, contract={detail.contract_no}, month={detail.detail_month}")
    return detail


# ═══════════════════════════════════════════════════════════════════
# Excel 导出
# ═══════════════════════════════════════════════════════════════════


async def get_monthly_export_data(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict:
    """获取月度台账导出原始数据。

    Returns:
        {contracts, month_detail_map, cum_map, current_month}
    """
    c_result = await db.execute(
        select(Contract).where(
            Contract.project_id == project_id,
            Contract.deleted_at.is_(None),
        ).order_by(Contract.ledger_group, Contract.review_mode, Contract.contract_no)
    )
    contracts = list(c_result.scalars().all())

    contract_nos = [c.contract_no for c in contracts]
    if not contract_nos:
        return {"contracts": [], "month_detail_map": {}, "cum_map": {}, "current_month": date.today()}

    today = date.today()
    current_month = date(today.year, today.month, 1)

    details_result = await db.execute(
        select(ContractMonthlyDetail).where(
            ContractMonthlyDetail.contract_no.in_(contract_nos),
            ContractMonthlyDetail.detail_month == current_month,
        )
    )
    month_detail_map = {d.contract_no: d for d in details_result.scalars().all()}

    cumulative_result = await db.execute(
        select(
            ContractMonthlyDetail.contract_no,
            func.coalesce(func.sum(ContractMonthlyDetail.output_amount), 0).label("cum_output"),
            func.coalesce(func.sum(ContractMonthlyDetail.payment_amount), 0).label("cum_payable"),
        )
        .where(ContractMonthlyDetail.contract_no.in_(contract_nos))
        .group_by(ContractMonthlyDetail.contract_no)
    )
    cum_map = {r[0]: (r[1], r[2]) for r in cumulative_result.all()}

    return {
        "contracts": contracts,
        "month_detail_map": month_detail_map,
        "cum_map": cum_map,
        "current_month": current_month,
    }


def _wan_yuan_or_blank(fen: int | None):
    """分 → 万元，0 返回空。"""
    if not fen:
        return None
    return round(fen_to_wan_yuan(fen), 4)


def build_monthly_excel(
    contracts: list[Contract],
    month_detail_map: dict[str, ContractMonthlyDetail],
    cum_map: dict[str, tuple[int, int]],
    current_month: date,
) -> io.BytesIO:
    """根据查询数据构建二类费用台账 Excel。

    布局：
    - 按 ledger_group 分组（建安合计 / 设备合计 / 二类费用合计 / 不计入台账）
    - 每个分组：标题行 → 表头 → 数据行（每合同一行）→ 小计行
    - 列：序号 | 合同编号 | 合同名称 | 供应商 | 合同金额(万元) |
           当月产值(万元) | 累计产值(万元) | 当月应付(万元) | 累计应付(万元) |
           完成比例 | 分项明细(分项名:产值/应付, ...)
    """
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "二类费用台账"

    if not contracts:
        ws.cell(row=1, column=1, value="暂无数据")
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    # ── 样式 ──
    title_font = Font(name="微软雅黑", size=14, bold=True)
    header_font = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    data_font = Font(name="微软雅黑", size=10)
    subtotal_fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
    subtotal_font = Font(name="微软雅黑", size=10, bold=True)
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)
    right_align = Alignment(horizontal="right", vertical="center")

    HEADERS = [
        "序号", "合同编号", "合同名称", "供应商", "合同金额\n(万元)",
        "当月产值\n(万元)", "累计产值\n(万元)", "当月应付\n(万元)", "累计应付\n(万元)",
        "完成比例", "分项明细",
    ]
    COL_WIDTHS = [6, 14, 24, 20, 14, 14, 14, 14, 14, 10, 50]

    row = 1

    # ── 大标题 ──
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=len(HEADERS))
    title_cell = ws.cell(row=row, column=1, value=f"二类费用台账（{current_month.strftime('%Y年%m月')}）")
    title_cell.font = title_font
    title_cell.alignment = center_align
    row += 2

    # ── 按 ledger_group 分组 ──
    ledger_group_order = [
        "construction", "equipment", "service",
    ]
    ledger_group_label: dict[str, str] = {
        "construction": "建安合计", "equipment": "设备合计",
        "service": "二类费用合计",
    }
    grouped: dict[str, list[Contract]] = {}
    for c in contracts:
        lg = c.ledger_group or "none"
        grouped.setdefault(lg, []).append(c)

    seq = 1

    for lg in ledger_group_order:
        items = grouped.pop(lg, [])
        if not items:
            continue
        row = _write_group(
            ws, row, lg, ledger_group_label.get(lg, lg), items,
            month_detail_map, cum_map, seq, HEADERS, COL_WIDTHS,
            title_font, header_font, header_fill, data_font,
            subtotal_fill, subtotal_font, thin_border,
            center_align, left_align, right_align,
        )
        seq += len(items)
        row += 1  # 分组间隔行

    # 剩余不计入台账的
    for lg, items in grouped.items():
        row = _write_group(
            ws, row, lg, lg, items,
            month_detail_map, cum_map, seq, HEADERS, COL_WIDTHS,
            title_font, header_font, header_fill, data_font,
            subtotal_fill, subtotal_font, thin_border,
            center_align, left_align, right_align,
        )
        seq += len(items)
        row += 1

    # ── 冻结 + 打印 ──
    ws.freeze_panes = "A4"
    ws.sheet_properties.pageSetUpPr = None

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def _write_group(
    ws, row, sub_type: str, label: str,
    items: list[Contract],
    month_detail_map: dict[str, ContractMonthlyDetail],
    cum_map: dict[str, tuple[int, int]],
    seq: int,
    HEADERS: list[str],
    COL_WIDTHS: list[int],
    title_font, header_font, header_fill, data_font,
    subtotal_fill, subtotal_font, thin_border,
    center_align, left_align, right_align,
) -> int:
    """写入一个 ledger_group 分组，返回下一可用行号。"""
    from openpyxl.utils import get_column_letter

    # ── 分组标题 ──
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=len(HEADERS))
    group_title = ws.cell(row=row, column=1, value=f"▌ {label}")
    group_title.font = title_font
    group_title.alignment = Alignment(horizontal="left", vertical="center")
    row += 1

    # ── 表头 ──
    for ci, h in enumerate(HEADERS, 1):
        cell = ws.cell(row=row, column=ci, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    for ci, w in enumerate(COL_WIDTHS, 1):
        ws.column_dimensions[get_column_letter(ci)].width = w
    row += 1

    # ── 数据行 ──
    group_monthly_output = 0
    group_cumulative_output = 0
    group_monthly_payable = 0
    group_cumulative_payable = 0

    for i, c in enumerate(items):
        idx = seq + i
        d = month_detail_map.get(c.contract_no)
        cum_out, cum_pay = cum_map.get(c.contract_no, (0, 0))

        m_output = d.output_amount or 0 if d else 0
        m_payable = d.payment_amount or 0 if d else 0
        group_monthly_output += m_output
        group_cumulative_output += cum_out
        group_monthly_payable += m_payable
        group_cumulative_payable += cum_pay

        # 分项明细文本
        fee_text = ""
        if d and d.cost_items_detail and isinstance(d.cost_items_detail, dict):
            items_list = d.cost_items_detail.get("items", [])
            if isinstance(items_list, list):
                parts = []
                for fi in items_list:
                    if isinstance(fi, dict):
                        name = fi.get("name", "")
                        output_w = _wan_yuan_or_blank(fi.get("output"))
                        payable_w = _wan_yuan_or_blank(fi.get("payable"))
                        parts.append(f"{name}:{output_w}/{payable_w}")
                fee_text = "| ".join(parts)

        row_data = [
            idx,
            c.contract_no,
            c.contract_desc,
            c.supplier_name,
            _wan_yuan_or_blank(c.contract_amount),
            _wan_yuan_or_blank(m_output),
            _wan_yuan_or_blank(cum_out),
            _wan_yuan_or_blank(m_payable),
            _wan_yuan_or_blank(cum_pay),
            f"{float(d.completed_ratio) * 100:.2f}%" if (d and d.completed_ratio is not None) else "",
            fee_text,
        ]

        for ci, val in enumerate(row_data, 1):
            cell = ws.cell(row=row, column=ci, value=val)
            cell.font = data_font
            cell.border = thin_border
            if ci in (1,):
                cell.alignment = center_align
            elif ci in (5, 6, 7, 8, 9, 10):
                cell.alignment = right_align
                if isinstance(val, (int, float)):
                    cell.number_format = "#,##0.0000"
            elif ci == 11:
                cell.alignment = left_align
            else:
                cell.alignment = left_align
        row += 1

    # ── 小计行 ──
    subtotal_data: list = [
        "", "", f"{label} 小计", "",
        "",  # 合同金额不汇总（各合同独立）
        _wan_yuan_or_blank(group_monthly_output),
        _wan_yuan_or_blank(group_cumulative_output),
        _wan_yuan_or_blank(group_monthly_payable),
        _wan_yuan_or_blank(group_cumulative_payable),
        "", "",
    ]
    for ci, val in enumerate(subtotal_data, 1):
        cell = ws.cell(row=row, column=ci, value=val)
        cell.font = subtotal_font
        cell.fill = subtotal_fill
        cell.border = thin_border
        if ci == 3:
            cell.alignment = left_align
        elif val != "":
            cell.alignment = right_align
            if isinstance(val, (int, float)):
                cell.number_format = "#,##0.0000"
        else:
            cell.alignment = center_align
    row += 1

    return row
