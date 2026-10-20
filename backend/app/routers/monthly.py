"""月度台账路由

接口：
- GET  /api/v1/projects/{project_id}/monthly             按月份分组台账列表
- POST /api/v1/contracts/{contract_id}/monthly-detail     手动更新审定台账
- PATCH /api/v1/monthly/{detail_id}/revoke                撤回确认（manual+confirmed→pending）
- GET  /api/v1/projects/{project_id}/monthly/export       导出 Excel
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.common import MessageResponse
from app.schemas.contract import MonthlyDetailResponse
from app.schemas.monthly import MonthlyListResponse, MonthlyManualUpdate
from app.services import monthly as monthly_service

router = APIRouter(tags=["月度台账"])


# ═══════════════════════════════════════════════════════════════════
# 1. 台账列表
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/projects/{project_id}/monthly",
    response_model=MonthlyListResponse,
)
async def get_monthly_list(
    project_id: uuid.UUID,
    month: str | None = Query(None, description="筛选月份（YYYY-MM），不传返回所有月份"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """按月份分组查询项目月度台账列表。

    返回每合同当月/累计的产值、应付、完成率及分项明细。
    cumulative 为项目下合同所有月份的总和。
    """
    from datetime import date as date_type

    month_date: date_type | None = None
    if month:
        month_date = date_type.fromisoformat(month + "-01")

    data = await monthly_service.get_project_monthly_list(db, project_id, month_date)
    return MonthlyListResponse(**data)


# ═══════════════════════════════════════════════════════════════════
# 2. 手动更新台账
# ═══════════════════════════════════════════════════════════════════

@router.post(
    "/contracts/{contract_id}/monthly-detail",
    response_model=MonthlyDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def manual_upsert_monthly_detail(
    contract_id: uuid.UUID,
    data: MonthlyManualUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """手动更新/创建月度台账明细（source=manual，需 operator 及以上权限）。

    可覆写已有 auto 记录；已有 manual 记录直接更新。
    金额单位统一为分。
    """
    detail = await monthly_service.manual_upsert_monthly_detail(
        db, contract_id, data.model_dump(),
    )
    return MonthlyDetailResponse.model_validate(detail)


# ═══════════════════════════════════════════════════════════════════
# 3. 撤回确认
# ═══════════════════════════════════════════════════════════════════

@router.patch(
    "/monthly/{detail_id}/revoke",
    response_model=MessageResponse,
)
async def revoke_monthly_detail(
    detail_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """撤回月度台账确认（需 operator 及以上权限）。

    约束：
    - 仅 source=manual 的台账允许撤回
    - 仅 status=confirmed 允许撤回 → 改为 pending
    """
    detail = await monthly_service.revoke_monthly_detail(db, detail_id)
    return MessageResponse(
        message=f"台账 {detail.contract_no} ({detail.detail_month}) 已撤回",
        detail=f"状态: confirmed → pending",
    )


# ═══════════════════════════════════════════════════════════════════
# 4. Excel 导出
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/projects/{project_id}/monthly/export",
)
async def export_monthly(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """导出项目二类费用台账 Excel。

    复刻二类费用台账格式：
    - 按 ledger_group 分组（建安合计/设备合计/二类费用合计/不计入台账）
    - 每分组：标题行 → 表头 → 数据行（每合同一行）→ 分组小计行
    - 金额统一万元格式化（4 位小数）
    - 分项明细列展示各分项产值/应付
    """
    export_data = await monthly_service.get_monthly_export_data(db, project_id)
    buf = monthly_service.build_monthly_excel(
        contracts=export_data["contracts"],
        month_detail_map=export_data["month_detail_map"],
        cum_map=export_data["cum_map"],
        current_month=export_data["current_month"],
    )

    month_str = export_data["current_month"].strftime("%Y%m")
    filename = f"二类费用台账_{month_str}.xlsx"

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
