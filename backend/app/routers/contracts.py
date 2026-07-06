"""合同路由：Contract + PaymentStage + NodeTemplate 完整 CRUD

路由设计对应业务文档 5.6 节：
- /api/v1/projects/{project_id}/contracts         → 项目下合同列表 + 新建
- /api/v1/contracts/{contract_id}                 → 合同详情/编辑/删除
- /api/v1/contracts/{contract_id}/nodes           → 支付节点 CRUD
- /api/v1/node-templates                          → 节点模板列表 + 创建
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.common import PaginatedResponse, MessageResponse
from app.schemas.contract import (
    ContractCreate,
    ContractUpdate,
    ContractResponse,
    ContractDetailResponse,
    PaymentStageCreate,
    PaymentStageUpdate,
    PaymentStageResponse,
    NodeTemplateCreate,
    NodeTemplateResponse,
    NodesFromTemplateCreate,
)
from app.services import contract as contract_service

router = APIRouter(tags=["合同管理"])


# ═══════════════════════════════════════════════════════════════════
# 合同 CRUD
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/projects/{project_id}/contracts",
    response_model=PaginatedResponse[ContractResponse],
)
async def list_contracts(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    contract_type: str | None = Query(None, description="按合同类型筛选：main/secondary/supplementary"),
    status: str | None = Query(None, description="按状态筛选：active/expired/terminated"),
    keyword: str | None = Query(None, description="搜索关键词（编号/供应商/描述）"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取项目下所有合同（分页+筛选）。"""
    items, total = await contract_service.get_contracts(
        db, project_id=project_id, page=page, page_size=page_size,
        contract_type=contract_type, status=status, keyword=keyword,
    )
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[ContractResponse.model_validate(c) for c in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )


@router.post(
    "/projects/{project_id}/contracts",
    response_model=ContractResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_contract(
    project_id: uuid.UUID,
    data: ContractCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """新建合同（需 operator 及以上权限）。"""
    contract = await contract_service.create_contract(db, project_id, data)
    return contract


@router.get("/contracts/{contract_id}", response_model=ContractDetailResponse)
async def get_contract(
    contract_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取合同详情（含支付节点列表）。"""
    contract = await contract_service.get_contract_detail(db, contract_id)
    if not contract:
        from app.core.exceptions import NotFound
        raise NotFound(detail="合同不存在")

    # 加载支付节点
    stages = await contract_service.get_payment_stages(db, contract_id)
    resp = ContractDetailResponse.model_validate(contract)
    resp.payment_stages = [PaymentStageResponse.model_validate(s) for s in stages]
    return resp


@router.put("/contracts/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: uuid.UUID,
    data: ContractUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """编辑合同（需 operator 及以上权限）。"""
    contract = await contract_service.update_contract(db, contract_id, data)
    if not contract:
        from app.core.exceptions import NotFound
        raise NotFound(detail="合同不存在")
    return contract


@router.delete("/contracts/{contract_id}", response_model=MessageResponse)
async def delete_contract(
    contract_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("admin")),
):
    """删除合同（软删除，需 admin 权限）。"""
    ok = await contract_service.delete_contract(db, contract_id)
    if not ok:
        from app.core.exceptions import NotFound
        raise NotFound(detail="合同不存在或已删除")
    return MessageResponse(message="合同已删除")


# ═══════════════════════════════════════════════════════════════════
# 支付节点 CRUD
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/contracts/{contract_id}/nodes",
    response_model=list[PaymentStageResponse],
)
async def list_payment_stages(
    contract_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取合同的所有支付节点（按 stage_order 排序）。"""
    stages = await contract_service.get_payment_stages(db, contract_id)
    return [PaymentStageResponse.model_validate(s) for s in stages]


@router.post(
    "/contracts/{contract_id}/nodes",
    response_model=PaymentStageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment_stage(
    contract_id: uuid.UUID,
    data: PaymentStageCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """手动添加支付节点（需 operator 及以上权限）。"""
    stage = await contract_service.create_payment_stage(db, contract_id, data)
    return stage


@router.put(
    "/contracts/{contract_id}/nodes/{node_id}",
    response_model=PaymentStageResponse,
)
async def update_payment_stage(
    contract_id: uuid.UUID,
    node_id: uuid.UUID,
    data: PaymentStageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """编辑支付节点（需 operator 及以上权限）。"""
    stage = await contract_service.update_payment_stage(db, node_id, data)
    if not stage:
        from app.core.exceptions import NotFound
        raise NotFound(detail="支付节点不存在")
    return stage


@router.delete(
    "/contracts/{contract_id}/nodes/{node_id}",
    response_model=MessageResponse,
)
async def delete_payment_stage(
    contract_id: uuid.UUID,
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """删除支付节点（需 operator 及以上权限）。"""
    ok = await contract_service.delete_payment_stage(db, node_id)
    if not ok:
        from app.core.exceptions import NotFound
        raise NotFound(detail="支付节点不存在")
    return MessageResponse(message="支付节点已删除")


@router.patch(
    "/contracts/{contract_id}/nodes/{node_id}/complete",
    response_model=PaymentStageResponse,
)
async def toggle_node_complete(
    contract_id: uuid.UUID,
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """标记/取消标记支付节点完成（用户手动确认外部事件如竣工验收）。"""
    stage = await contract_service.complete_payment_stage(db, node_id)
    if not stage:
        from app.core.exceptions import NotFound
        raise NotFound(detail="支付节点不存在")
    return stage


@router.post(
    "/contracts/{contract_id}/nodes/from-template",
    response_model=list[PaymentStageResponse],
    status_code=status.HTTP_201_CREATED,
)
async def generate_nodes_from_template(
    contract_id: uuid.UUID,
    data: NodesFromTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """从模板一键生成支付节点（需 operator 及以上权限）。

    先检查合同是否已有节点，有则拒绝。
    生成的节点可后续手动微调。
    """
    stages = await contract_service.generate_nodes_from_template(db, contract_id, data)
    return [PaymentStageResponse.model_validate(s) for s in stages]


# ═══════════════════════════════════════════════════════════════════
# 节点模板
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/node-templates",
    response_model=PaginatedResponse[NodeTemplateResponse],
)
async def list_node_templates(
    biz_type: str | None = Query(None, description="按业务类型筛选: supervision/design/testing/construction/custom"),
    is_preset: bool | None = Query(None, description="按是否预置筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取节点模板列表（分页筛选）。"""
    items, total = await contract_service.get_node_templates(
        db, biz_type=biz_type, is_preset=is_preset, page=page, page_size=page_size,
    )
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[NodeTemplateResponse.model_validate(t) for t in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )


@router.post(
    "/node-templates",
    response_model=NodeTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_node_template(
    data: NodeTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """创建用户自定义节点模板（需 operator 及以上权限）。"""
    template = await contract_service.create_node_template(db, data)
    return template
