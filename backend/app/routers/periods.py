"""报送期次路由：ReportingPeriod CRUD + 审核草稿自动生成 + 汇总表导出 (Phase2)

路由设计：
- GET    /api/v1/projects/{project_id}/periods           → 期次列表
- POST   /api/v1/projects/{project_id}/periods           → 创建期次（自动生成审核草稿）
- GET    /api/v1/periods/{period_id}                     → 期次详情
- PATCH  /api/v1/periods/{period_id}                     → 更新期次
- PATCH  /api/v1/periods/{period_id}/status              → 期次状态变更
- DELETE /api/v1/periods/{period_id}                     → 删除期次
- GET    /api/v1/periods/{period_id}/export              → 导出审核汇总表 Excel
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.common import PaginatedResponse
from app.schemas.period import PeriodCreate, PeriodUpdate, PeriodStatusUpdate, PeriodResponse, PeriodDetailResponse
from app.services import period_service
from app.services import export as export_service

router = APIRouter(tags=["报送期次"])


@router.get(
    "/projects/{project_id}/periods",
    response_model=PaginatedResponse[PeriodResponse],
)
async def list_periods(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    status: str | None = Query(None, description="按期次状态筛选：draft/in_progress/reviewed/closed"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取项目下的期次列表（分页+筛选）。"""
    items, total = await period_service.get_periods(
        db, project_id=project_id, page=page, page_size=page_size, status=status,
    )
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[PeriodResponse.model_validate(p) for p in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )


@router.post(
    "/projects/{project_id}/periods",
    response_model=PeriodDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_period(
    project_id: uuid.UUID,
    data: PeriodCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """创建期次（需 operator 权限）。

    会自动执行：
    1. 写入 t_period_contracts 关联
    2. 为每个合同生成 draft 状态的审核记录
    3. 为每条审核记录复制合同的费用分项模板快照
    """
    period = await period_service.create_period(
        db,
        project_id=project_id,
        period_month=data.period_month,
        period_no=data.period_no,
        contract_ids=data.contract_ids,
        remark=data.remark,
    )
    # 重新加载含关联数据
    period = await period_service.get_period(db, period.id)
    return PeriodDetailResponse(
        id=period.id,
        project_id=period.project_id,
        period_no=period.period_no,
        period_month=period.period_month,
        status=period.status,
        remark=period.remark,
        created_at=period.created_at,
        updated_at=period.updated_at,
        contract_count=getattr(period, "contract_count", 0),
        review_count=getattr(period, "review_count", 0),
        contract_ids=getattr(period, "contract_ids", data.contract_ids),
    )


@router.get("/periods/{period_id}", response_model=PeriodDetailResponse)
async def get_period(
    period_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取期次详情（含关联合同列表和统计信息）。"""
    period = await period_service.get_period(db, period_id)
    if not period:
        from app.core.exceptions import NotFound
        raise NotFound(detail="期次不存在")

    return PeriodDetailResponse(
        id=period.id,
        project_id=period.project_id,
        period_no=period.period_no,
        period_month=period.period_month,
        status=period.status,
        remark=period.remark,
        created_at=period.created_at,
        updated_at=period.updated_at,
        contract_count=getattr(period, "contract_count", 0),
        review_count=getattr(period, "review_count", 0),
        contract_ids=getattr(period, "contract_ids", []),
    )


@router.patch("/periods/{period_id}", response_model=PeriodResponse)
async def update_period(
    period_id: uuid.UUID,
    data: PeriodUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """更新期次信息（仅 draft 状态可编辑，需 operator 权限）。"""
    period = await period_service.update_period(
        db,
        period_id=period_id,
        period_month=data.period_month,
        contract_ids=data.contract_ids,
        remark=data.remark,
    )
    if not period:
        from app.core.exceptions import NotFound
        raise NotFound(detail="期次不存在")
    return period


@router.patch("/periods/{period_id}/status", response_model=PeriodResponse)
async def update_period_status(
    period_id: uuid.UUID,
    data: PeriodStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """更新期次状态（需 operator 权限）。

    状态流转：draft → submitted → reviewed → closed（支持回退到 draft）
    """
    period = await period_service.update_period_status(db, period_id, data.status)
    if not period:
        from app.core.exceptions import NotFound
        raise NotFound(detail="期次不存在")
    return period


@router.delete("/periods/{period_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_period(
    period_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("admin")),
):
    """删除期次（仅 admin 权限，仅 draft 状态可删）。

    级联删除：关联的审核记录 + 费用分项 + 合同关联。
    """
    deleted = await period_service.delete_period(db, period_id)
    if not deleted:
        from app.core.exceptions import NotFound
        raise NotFound(detail="期次不存在")


# ═══════════════════════════════════════════════════════════════════
# 审核汇总表导出
# ═══════════════════════════════════════════════════════════════════

@router.get("/periods/{period_id}/export")
async def export_period_summary(
    period_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """导出审核汇总表 Excel（多 Sheet）。

    Sheet 结构：
    - 封面：项目信息 + 承包单位概览
    - 建安费用汇总：daily_aggregate 合同的审定值汇总
    - 供应商分表：每个 node_judge 合同一张独立 Sheet，含费用分项明细

    复刻真实汇总表格式。
    """
    data = await export_service._get_period_export_data(db, period_id)
    period = data["period"]
    buf = export_service.build_period_export_excel(data)

    filename = f"审核汇总表_第{period.period_no}期_{period.period_month}.xlsx"
    # RFC 5987 编码中文文件名
    from urllib.parse import quote
    encoded = quote(filename)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded}",
        },
    )
