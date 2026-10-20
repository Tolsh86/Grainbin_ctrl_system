"""项目 CRUD + 基础统计业务逻辑"""

from __future__ import annotations

import uuid
from datetime import UTC, date as date_type, datetime

from dateutil.relativedelta import relativedelta
from loguru import logger
from sqlalchemy import cast, func, select, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contract
from app.models.data_row import DataRow
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectStatsResponse
from app.utils.db import paginate


def _compute_end_date(start_date: date_type, duration_months: int) -> date_type:
    """根据起始月和持续月数计算结束月。

    end_date = start_date + duration_months - 1 个月
    """
    s = date_type(start_date.year, start_date.month, 1)
    return s + relativedelta(months=duration_months - 1)


def _compute_construction_period(start_date: date_type, duration_months: int) -> str:
    """根据起始月和持续月数推算建设周期（起止年）。

    格式：YYYY-YYYY，如 start=2026.07, duration=24 → "2026-2028"
    """
    s = date_type(start_date.year, start_date.month, 1)
    e = s + relativedelta(months=duration_months - 1)
    return f"{s.year}-{e.year}"


async def get_projects(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    project_nature: str | None = None,
    invest_timing: str | None = None,
    region: str | None = None,
    keyword: str | None = None,
) -> tuple[list[Project], int]:
    """分页查询项目列表，支持多维度筛选。"""
    stmt = select(Project).order_by(Project.created_at.desc())
    count_stmt = select(func.count(Project.id))

    if status:
        stmt = stmt.where(Project.project_status == status)
        count_stmt = count_stmt.where(Project.project_status == status)
    if project_nature:
        stmt = stmt.where(Project.project_nature == project_nature)
        count_stmt = count_stmt.where(Project.project_nature == project_nature)
    if invest_timing:
        stmt = stmt.where(Project.invest_timing == invest_timing)
        count_stmt = count_stmt.where(Project.invest_timing == invest_timing)
    if region:
        stmt = stmt.where(Project.region == region)
        count_stmt = count_stmt.where(Project.region == region)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(Project.project_name.ilike(like) | Project.project_code.ilike(like))
        count_stmt = count_stmt.where(Project.project_name.ilike(like) | Project.project_code.ilike(like))

    return await paginate(db, stmt, page=page, page_size=page_size, model=Project, count_stmt=count_stmt)


async def get_project(db: AsyncSession, project_id: uuid.UUID) -> Project | None:
    """按 ID 获取项目。"""
    result = await db.execute(select(Project).where(Project.id == project_id, Project.deleted_at.is_(None)))
    return result.scalar_one_or_none()


async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
    """创建新项目。project_code 为空时自动生成 PJ-YYYYMMDD-NNN。

    自动从 start_date + duration_months 计算 end_date。
    如果未传 start_date，默认使用当月 1 日。
    """
    vals = data.model_dump(exclude={"start_date", "duration_months"})

    # ── 自动生成 start_date + end_date + construction_period ──
    start = data.start_date or date_type.today().replace(day=1)
    vals["start_date"] = start
    vals["end_date"] = _compute_end_date(start, data.duration_months)
    vals["construction_period"] = _compute_construction_period(start, data.duration_months)

    # ── 自动生成 project_code ──
    if not vals.get("project_code", "").strip():
        today = date_type.today()
        today_str = today.strftime("%Y%m%d")
        result = await db.execute(
            select(func.count(Project.id)).where(
                func.date(Project.created_at) == today
            )
        )
        seq = (result.scalar() or 0) + 1
        vals["project_code"] = f"PJ-{today_str}-{seq:03d}"

    project = Project(**vals)
    db.add(project)
    await db.flush()
    await db.refresh(project)
    logger.info(f"项目创建成功: id={project.id}, code={project.project_code}, period={vals['start_date']} ~ {vals['end_date']}")
    return project


async def update_project(db: AsyncSession, project_id: uuid.UUID, data: ProjectUpdate) -> Project | None:
    """更新项目。

    如果传了 start_date + duration_months，自动计算 end_date。
    """
    project = await get_project(db, project_id)
    if not project:
        return None

    update_data = data.model_dump(exclude_unset=True)

    # ── 自动计算 end_date + construction_period（如果传了 start_date + duration_months） ──
    if "start_date" in update_data and "duration_months" in update_data:
        if update_data["start_date"] is not None and update_data["duration_months"] is not None:
            sd = update_data.pop("start_date")
            dm = update_data.pop("duration_months")
            update_data["start_date"] = sd
            update_data["end_date"] = _compute_end_date(sd, dm)
            update_data["construction_period"] = _compute_construction_period(sd, dm)
        else:
            # 传了但为空，忽略
            update_data.pop("start_date", None)
            update_data.pop("duration_months", None)
    else:
        # 只传了 start_date 或 duration_months 之一，不完整，忽略
        update_data.pop("start_date", None)
        update_data.pop("duration_months", None)

    for key, value in update_data.items():
        setattr(project, key, value)
    await db.flush()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project_id: uuid.UUID) -> bool:
    """软删除项目。"""
    project = await get_project(db, project_id)
    if not project:
        return False
    project.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


async def get_project_stats(db: AsyncSession) -> ProjectStatsResponse:
    """获取项目基础统计数据。"""
    # 总数
    total = (await db.execute(
        select(func.count(Project.id)).where(Project.deleted_at.is_(None)))
    ).scalar_one()

    # 按状态分组
    rows = (await db.execute(
        select(Project.project_status, func.count(Project.id))
        .where(Project.deleted_at.is_(None))
        .group_by(Project.project_status)
    )).all()
    by_status = {r[0]: r[1] for r in rows}

    # 按性质分组
    rows = (await db.execute(
        select(Project.project_nature, func.count(Project.id))
        .where(Project.deleted_at.is_(None))
        .group_by(Project.project_nature)
    )).all()
    by_nature = {r[0]: r[1] for r in rows}

    # 按区域分组
    rows = (await db.execute(
        select(Project.region, func.count(Project.id))
        .where(Project.deleted_at.is_(None))
        .group_by(Project.region)
    )).all()
    by_region = {r[0]: r[1] for r in rows}

    # 总投资合计
    total_investment = (await db.execute(
        select(func.coalesce(func.sum(Project.planned_total_invest), 0))
        .where(Project.deleted_at.is_(None))
    )).scalar_one()

    return ProjectStatsResponse(
        total=total,
        by_status=by_status,
        by_nature=by_nature,
        by_region=by_region,
        total_investment=total_investment,
    )


# ══════════════════════════════════════════════════════════════
# 项目数据行查询
# ══════════════════════════════════════════════════════════════

EXPORT_MAX_ROWS = 100_000


async def get_data_rows(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 20,
    category: str | None = None,
    keyword: str | None = None,
    cost_type: str | None = None,
    is_confirmed: bool | None = None,
    data_date_from: date | None = None,
    data_date_to: date | None = None,
    # ── V2.2 第二阶段新增筛选 ──
    contract_id: uuid.UUID | None = None,
    cost_sub_type: str | None = None,
    status: str | None = None,
    month: date | None = None,
) -> tuple[list[DataRow], int]:
    """分页查询项目下的数据行，支持多维度筛选。"""
    stmt = (
        select(DataRow)
        .where(DataRow.project_id == project_id, DataRow.deleted_at.is_(None))
        .order_by(DataRow.created_at.desc())
    )
    count_stmt = select(func.count(DataRow.id)).where(
        DataRow.project_id == project_id, DataRow.deleted_at.is_(None),
    )

    if category:
        stmt = stmt.where(DataRow.category == category)
        count_stmt = count_stmt.where(DataRow.category == category)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(DataRow.item_name.ilike(like) | DataRow.category.ilike(like))
        count_stmt = count_stmt.where(DataRow.item_name.ilike(like) | DataRow.category.ilike(like))
    if cost_type:
        stmt = stmt.where(DataRow.cost_type == cost_type)
        count_stmt = count_stmt.where(DataRow.cost_type == cost_type)
    if is_confirmed is not None:
        stmt = stmt.where(DataRow.is_confirmed == is_confirmed)
        count_stmt = count_stmt.where(DataRow.is_confirmed == is_confirmed)
    if data_date_from:
        stmt = stmt.where(DataRow.data_date >= data_date_from)
        count_stmt = count_stmt.where(DataRow.data_date >= data_date_from)
    if data_date_to:
        stmt = stmt.where(DataRow.data_date <= data_date_to)
        count_stmt = count_stmt.where(DataRow.data_date <= data_date_to)
    # ── V2.2 第二阶段新增筛选 ──
    if contract_id:
        stmt = stmt.where(DataRow.contract_id == contract_id)
        count_stmt = count_stmt.where(DataRow.contract_id == contract_id)
    if cost_sub_type:
        stmt = stmt.where(DataRow.cost_sub_type == cost_sub_type)
        count_stmt = count_stmt.where(DataRow.cost_sub_type == cost_sub_type)
    if status:
        stmt = stmt.where(DataRow.status == status)
        count_stmt = count_stmt.where(DataRow.status == status)
    if month:
        stmt = stmt.where(
            func.extract("year", DataRow.data_date) == month.year,
            func.extract("month", DataRow.data_date) == month.month,
        )
        count_stmt = count_stmt.where(
            func.extract("year", DataRow.data_date) == month.year,
            func.extract("month", DataRow.data_date) == month.month,
        )

    return await paginate(db, stmt, page=page, page_size=page_size, model=DataRow, count_stmt=count_stmt)


async def export_data_rows(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    category: str | None = None,
    keyword: str | None = None,
    cost_type: str | None = None,
    is_confirmed: bool | None = None,
    data_date_from: date | None = None,
    data_date_to: date | None = None,
) -> list[DataRow]:
    """导出项目下的数据行（上限 {EXPORT_MAX_ROWS} 行）。"""
    stmt = (
        select(DataRow)
        .where(DataRow.project_id == project_id, DataRow.deleted_at.is_(None))
        .order_by(DataRow.created_at.desc())
        .limit(EXPORT_MAX_ROWS)
    )

    if category:
        stmt = stmt.where(DataRow.category == category)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(DataRow.item_name.ilike(like) | DataRow.category.ilike(like))
    if cost_type:
        stmt = stmt.where(DataRow.cost_type == cost_type)
    if is_confirmed is not None:
        stmt = stmt.where(DataRow.is_confirmed == is_confirmed)
    if data_date_from:
        stmt = stmt.where(DataRow.data_date >= data_date_from)
    if data_date_to:
        stmt = stmt.where(DataRow.data_date <= data_date_to)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def aggregate_data_rows(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    category: str | None = None,
    cost_type: str | None = None,
    contract_id: uuid.UUID | None = None,
    month: date | None = None,
) -> list[dict]:
    """按月、合同分组聚合数据行的产值 sum(amount)。

    返回 [{month, contract_id, contract_no, total_amount, row_count}, ...]。
    """
    year_month = func.to_char(DataRow.data_date, "YYYY-MM")

    stmt = (
        select(
            year_month.label("month"),
            DataRow.contract_id,
            Contract.contract_no,
            func.coalesce(func.sum(DataRow.amount), 0).label("total_amount"),
            func.count(DataRow.id).label("row_count"),
        )
        .outerjoin(Contract, DataRow.contract_id == Contract.id)
        .where(DataRow.project_id == project_id, DataRow.deleted_at.is_(None))
        .group_by(year_month, DataRow.contract_id, Contract.contract_no)
        .order_by(year_month.desc(), DataRow.contract_id)
    )

    if category:
        stmt = stmt.where(DataRow.category == category)
    if cost_type:
        stmt = stmt.where(DataRow.cost_type == cost_type)
    if contract_id:
        stmt = stmt.where(DataRow.contract_id == contract_id)
    if month:
        stmt = stmt.where(
            cast(func.extract("year", DataRow.data_date), String) == str(month.year),
            cast(func.extract("month", DataRow.data_date), String) == str(month.month),
        )

    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "month": r.month,
            "contract_id": r.contract_id,
            "contract_no": r.contract_no,
            "total_amount": r.total_amount or 0,
            "row_count": r.row_count,
        }
        for r in rows
    ]


async def update_data_row_status(
    db: AsyncSession,
    row_id: uuid.UUID,
    status: str,
    remark: str | None = None,
) -> DataRow | None:
    """仅修改数据行的审核状态。remark 暂存入 raw_data 字段。"""
    result = await db.execute(
        select(DataRow).where(DataRow.id == row_id, DataRow.deleted_at.is_(None))
    )
    row = result.scalar_one_or_none()
    if not row:
        return None

    row.status = status
    if remark:
        raw = dict(row.raw_data) if row.raw_data else {}
        raw["status_remark"] = remark
        raw["status_updated_at"] = datetime.now(UTC).isoformat()
        row.raw_data = raw

    await db.flush()
    await db.refresh(row)
    logger.info(f"数据行状态更新: id={row_id}, status={status}, remark={remark}")
    return row
