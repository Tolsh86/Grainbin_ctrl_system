"""项目 CRUD + 基础统计业务逻辑"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectStatsResponse
from app.utils.db import paginate


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
    """创建新项目。"""
    project = Project(**data.model_dump())
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def update_project(db: AsyncSession, project_id: uuid.UUID, data: ProjectUpdate) -> Project | None:
    """更新项目。"""
    project = await get_project(db, project_id)
    if not project:
        return None
    update_data = data.model_dump(exclude_unset=True)
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
