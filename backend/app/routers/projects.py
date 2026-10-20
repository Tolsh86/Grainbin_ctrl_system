"""项目路由：完整 CRUD + 筛选 + 基础统计"""

import csv
import io
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.common import PaginatedResponse, MessageResponse
from app.schemas.data_row import DataCreate, DataRowAggregateItem, DataRowResponse, DataRowStatusUpdate
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


# ── 项目数据行查询 ──────────────────────────────

_DATA_ROW_CSV_HEADERS = [
    "id", "project_id", "data_date", "category", "item_name",
    "planned_quantity", "actual_quantity", "unit", "unit_price(分)",
    "amount(分)", "cost_type", "source_doc", "source_type",
    "is_confirmed", "confirmed_by", "confirmed_at", "created_at", "updated_at",
]


@router.get("/{project_id}/data-rows", response_model=PaginatedResponse[DataRowResponse])
async def list_data_rows(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=200, description="每页条数"),
    category: str | None = Query(None, description="按分部工程类别筛选"),
    keyword: str | None = Query(None, description="搜索关键词（分项名称/类别）"),
    cost_type: str | None = Query(None, description="按费用类型筛选"),
    is_confirmed: bool | None = Query(None, description="按确认状态筛选"),
    data_date_from: date | None = Query(None, description="数据日期起"),
    data_date_to: date | None = Query(None, description="数据日期止"),
    # ── V2.2 第二阶段新增筛选 ──
    contract_id: uuid.UUID | None = Query(None, description="按关联合同筛选"),
    cost_sub_type: str | None = Query(None, description="按费用分项类型筛选"),
    row_status: str | None = Query(None, alias="status", description="按审核状态筛选：draft/submitted/reviewed/rejected/confirmed"),
    month: date | None = Query(None, description="按月份筛选（如 2026-01-01），匹配 data_date 的年份和月份"),
    format: str | None = Query(None, description="导出格式：csv 导出 CSV 文件"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取项目下的数据行（分页+多维度筛选+CSV 导出）。

    支持按类别、费用类型、确认状态、日期范围、合同、费用分项、审核状态、月份筛选，以及关键词搜索。
    传入 ``format=csv`` 时返回 CSV 文件流（上限 10 万行）。
    """
    # ── CSV 导出 ──────────────────────────────────
    if format == "csv":
        rows = await project_service.export_data_rows(
            db, project_id,
            category=category, keyword=keyword, cost_type=cost_type,
            is_confirmed=is_confirmed,
            data_date_from=data_date_from, data_date_to=data_date_to,
        )
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(_DATA_ROW_CSV_HEADERS)
        for row in rows:
            writer.writerow([
                str(row.id), str(row.project_id), row.data_date, row.category,
                row.item_name, row.planned_quantity, row.actual_quantity, row.unit,
                row.unit_price, row.amount, row.cost_type, row.source_doc,
                row.source_type, row.is_confirmed,
                str(row.confirmed_by) if row.confirmed_by else "",
                row.confirmed_at.isoformat() if row.confirmed_at else "",
                row.created_at.isoformat() if row.created_at else "",
                row.updated_at.isoformat() if row.updated_at else "",
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=data-rows-{project_id}.csv"},
        )

    # ── 分页查询 ──────────────────────────────────
    # 检查项目是否存在
    project = await project_service.get_project(db, project_id)
    if not project:
        from app.core.exceptions import NotFound
        raise NotFound(detail="项目不存在")

    items, total = await project_service.get_data_rows(
        db, project_id,
        page=page, page_size=page_size,
        category=category, keyword=keyword, cost_type=cost_type,
        is_confirmed=is_confirmed,
        data_date_from=data_date_from, data_date_to=data_date_to,
        contract_id=contract_id, cost_sub_type=cost_sub_type,
        status=row_status, month=month,
    )
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[DataRowResponse.model_validate(r) for r in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )


@router.get("/{project_id}/data-rows/aggregate", response_model=list[DataRowAggregateItem])
async def aggregate_data_rows(
    project_id: uuid.UUID,
    category: str | None = Query(None, description="按分部工程类别筛选"),
    cost_type: str | None = Query(None, description="按费用类型筛选"),
    contract_id: uuid.UUID | None = Query(None, description="按关联合同筛选"),
    month: date | None = Query(None, description="按月份筛选"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """按月、合同分组聚合项目数据行的产值 sum(amount)。"""
    # 检查项目是否存在
    project = await project_service.get_project(db, project_id)
    if not project:
        from app.core.exceptions import NotFound
        raise NotFound(detail="项目不存在")

    rows = await project_service.aggregate_data_rows(
        db, project_id,
        category=category, cost_type=cost_type,
        contract_id=contract_id, month=month,
    )
    return [DataRowAggregateItem(**r) for r in rows]


@router.patch("/data-rows/{row_id}/status", response_model=DataRowResponse)
async def update_data_row_status(
    row_id: uuid.UUID,
    data: DataRowStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """仅修改数据行的审核状态（需 operator 权限）。备注存入 raw_data。"""
    row = await project_service.update_data_row_status(
        db, row_id, status=data.status, remark=data.remark,
    )
    if not row:
        from app.core.exceptions import NotFound
        raise NotFound(detail="数据行不存在")
    return DataRowResponse.model_validate(row)
