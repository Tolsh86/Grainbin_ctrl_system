"""项目路由：完整 CRUD + 筛选 + 基础统计"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.common import PaginatedResponse, MessageResponse
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectStatsResponse
from app.services import project as project_service

router = APIRouter(prefix="/projects", tags=["项目管理"])


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    status: str | None = Query(None, description="按状态筛选：preparing/constructing/completed/suspended"),
    project_nature: str | None = Query(None, description="按项目性质筛选"),
    invest_timing: str | None = Query(None, description="按投资时序筛选"),
    region: str | None = Query(None, description="按区域筛选"),
    keyword: str | None = Query(None, description="搜索关键词（项目名称/编码）"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取项目列表（分页+多维度筛选）。"""
    items, total = await project_service.get_projects(
        db, page=page, page_size=page_size,
        status=status, project_nature=project_nature,
        invest_timing=invest_timing, region=region, keyword=keyword,
    )
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[ProjectResponse.model_validate(p) for p in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )


@router.get("/stats", response_model=ProjectStatsResponse)
async def get_project_stats(
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取项目基础统计数据。"""
    return await project_service.get_project_stats(db)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取单个项目详情。"""
    project = await project_service.get_project(db, project_id)
    if not project:
        from app.core.exceptions import NotFound
        raise NotFound(detail="项目不存在")
    return project


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """创建新项目（需 editor 及以上权限）。"""
    project = await project_service.create_project(db, data)
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """更新项目（需 editor 及以上权限）。"""
    project = await project_service.update_project(db, project_id, data)
    if not project:
        from app.core.exceptions import NotFound
        raise NotFound(detail="项目不存在")
    return project


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("admin")),
):
    """删除项目（软删除，需 admin 权限）。"""
    ok = await project_service.delete_project(db, project_id)
    if not ok:
        from app.core.exceptions import NotFound
        raise NotFound(detail="项目不存在或已删除")
    return MessageResponse(message="项目已删除")
