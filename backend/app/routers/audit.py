"""审核工作台路由

接口：
- GET  /api/v1/projects/{project_id}/audit/summary             当月合同待审/已审数量概览
- GET  /api/v1/projects/{project_id}/audit/contract/{contract_id} 合同审核详情（建安/咨询分叉）
- POST /api/v1/projects/{project_id}/audit/confirm             提交分项审定数据
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.audit import (
    AuditConfirmRequest,
    AuditSummaryResponse,
    ConstructionAuditResponse,
    ConsultingAuditResponse,
)
from app.schemas.contract import MonthlyDetailResponse
from app.services import audit as audit_service

router = APIRouter(tags=["审核工作台"])


def _current_month() -> date:
    """默认当月第一天。"""
    today = date.today()
    return date(today.year, today.month, 1)


# ═══════════════════════════════════════════════════════════════════
# 1. 当月合同审核概览
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/projects/{project_id}/audit/summary",
    response_model=AuditSummaryResponse,
)
async def get_audit_summary(
    project_id: uuid.UUID,
    month: date = Query(
        default_factory=_current_month,
        description="审核月份（如 2026-01-01），默认当月",
    ),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取项目当月合同待审/已审数量概览。"""
    return await audit_service.get_audit_summary(db, project_id, month)


# ═══════════════════════════════════════════════════════════════════
# 2. 合同审核详情
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/projects/{project_id}/audit/contract/{contract_id}",
    response_model=ConstructionAuditResponse | ConsultingAuditResponse,
)
async def get_audit_contract_detail(
    project_id: uuid.UUID,
    contract_id: uuid.UUID,
    month: date = Query(
        default_factory=_current_month,
        description="审核月份（如 2026-01-01），默认当月",
    ),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取合同审核详情。

    按合同 review_mode 自动分叉：
    - 日报聚合模式（daily_aggregate）：返回 DataRow 日报聚合分项
    - 节点判断模式（node_judge）：返回合同本身作为一条费用分项 + PaymentStage 节点累计产值
    - 无产值模式（none）：不支持审核工作台
    """
    return await audit_service.get_audit_contract_detail(db, contract_id, month)


# ═══════════════════════════════════════════════════════════════════
# 3. 审核确认
# ═══════════════════════════════════════════════════════════════════

@router.post(
    "/projects/{project_id}/audit/confirm",
    response_model=MonthlyDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def confirm_audit(
    project_id: uuid.UUID,
    data: AuditConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """提交分项审定数据，写入月度台账（需 operator 及以上权限）。

    校验：
    - 各分项 payable 之和不超过合同金额上限
    - 各分项 ratio 在 [0, 1]
    - 已有 source=manual 的记录不会被覆盖
    """
    items = [it.model_dump() for it in data.items]
    detail = await audit_service.confirm_audit(
        db,
        contract_id=data.contract_id,
        detail_month=data.detail_month,
        items=items,
        status=data.status,
    )
    return MonthlyDetailResponse.model_validate(detail)
