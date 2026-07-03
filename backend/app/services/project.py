"""项目 CRUD 业务逻辑"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


async def get_projects(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> tuple[list[Project], int]:
    """分页查询项目列表，可按状态筛选。"""
    query = select(Project).where(Project.deleted_at.is_(None))
    count_query = select(func.count(Project.id)).where(Project.deleted_at.is_(None))

    if status:
        query = query.where(Project.project_status == status)
        count_query = count_query.where(Project.project_status == status)

    total = (await db.execute(count_query)).scalar_one()
    items = (
        await db.execute(
            query.order_by(Project.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    return list(items), total


async def get_project(db: AsyncSession, project_id: uuid.UUID) -> Project | None:
    """按 ID 获取单个项目。"""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
    """创建新项目。"""
    project = Project(**data.model_dump())
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def update_project(
    db: AsyncSession, project_id: uuid.UUID, data: ProjectUpdate,
) -> Project | None:
    """更新项目（部分更新）。"""
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
