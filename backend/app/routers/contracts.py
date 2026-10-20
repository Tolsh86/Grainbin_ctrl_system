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
from app.schemas.fee_item import (
    ContractFeeItemCreate,
    ContractFeeItemUpdate,
    ContractFeeItemResponse,
)
from app.schemas.contract import (
    ContractCreate,
    ContractUpdate,
    ContractResponse,
    ContractDetailResponse,
    ContractGroupResponse,
    PaymentStageCreate,
    PaymentStageUpdate,
    PaymentStageResponse,
    NodeTemplateCreate,
    NodeTemplateResponse,
    NodesFromTemplateCreate,
    PaymentMatrixResponse,
)
from app.services import contract as contract_service
from app.services import fee_item_service

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


@router.get(
    "/projects/{project_id}/contracts/groups",
    response_model=list[ContractGroupResponse],
)
async def get_contract_groups(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """按 contract_group 分组返回项目下合同列表。"""
    groups = await contract_service.get_contract_groups(db, project_id)
    return [
        ContractGroupResponse(
            contract_group=g["contract_group"],
            contracts=[ContractResponse.model_validate(c) for c in g["contracts"]],
        )
        for g in groups
    ]


# ═══════════════════════════════════════════════════════════════════
# 支付节点 CRUD
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/projects/{project_id}/nodes",
    response_model=list[PaymentStageResponse],
)
async def list_project_payment_stages(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取项目下所有合同的支付节点（选择合同为空时展示全部）。"""
    stages = await contract_service.get_project_payment_stages(db, project_id)
    # 填充冗余的 supplier_name / contract_desc
    stages_resp = []
    for s in stages:
        r = PaymentStageResponse.model_validate(s)
        if s.contract:
            r.supplier_name = s.contract.supplier_name
            r.contract_desc = s.contract.contract_desc
        stages_resp.append(r)
    return stages_resp


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
    stages_resp = []
    for s in stages:
        r = PaymentStageResponse.model_validate(s)
        if s.contract:
            r.supplier_name = s.contract.supplier_name
            r.contract_desc = s.contract.contract_desc
        stages_resp.append(r)
    return stages_resp


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
# 费用分项 CRUD（Phase2 新增）
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/contracts/{contract_id}/fee-items",
    response_model=list[ContractFeeItemResponse],
)
async def list_contract_fee_items(
    contract_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取合同的费用分项列表。"""
    items = await fee_item_service.get_contract_fee_items(db, contract_id)
    return [ContractFeeItemResponse.model_validate(i) for i in items]


@router.post(
    "/contracts/{contract_id}/fee-items",
    response_model=list[ContractFeeItemResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_contract_fee_items(
    contract_id: uuid.UUID,
    items: list[ContractFeeItemCreate],
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """批量添加合同费用分项（需 operator 权限）。"""
    created = await fee_item_service.create_contract_fee_items(
        db, contract_id, [i.model_dump() for i in items]
    )
    return [ContractFeeItemResponse.model_validate(c) for c in created]


@router.put(
    "/contracts/{contract_id}/fee-items/{item_id}",
    response_model=ContractFeeItemResponse,
)
async def update_contract_fee_item(
    contract_id: uuid.UUID,
    item_id: uuid.UUID,
    data: ContractFeeItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """编辑费用分项（名称/金额/比例），需 operator 权限。"""
    updated = await fee_item_service.update_contract_fee_item(
        db, item_id, data.model_dump(exclude_unset=True)
    )
    if not updated:
        from app.core.exceptions import NotFound
        raise NotFound(detail="费用分项不存在")
    return updated


@router.delete(
    "/contracts/{contract_id}/fee-items/{item_id}",
    response_model=MessageResponse,
)
async def delete_contract_fee_item(
    contract_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """删除费用分项，需 operator 权限。

    已关联的审核快照 fee_item_id 会 ON DELETE SET NULL，审核记录不受影响。
    """
    ok = await fee_item_service.delete_contract_fee_item(db, item_id)
    if not ok:
        from app.core.exceptions import NotFound
        raise NotFound(detail="费用分项不存在")
    return MessageResponse(message="费用分项已删除")


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


# ═══════════════════════════════════════════════════════════════════
# 审核模式 & 台账分组（字典）
# ═══════════════════════════════════════════════════════════════════

_REVIEW_MODES = [
    {"value": "daily_aggregate", "label": "日报聚合模式", "description": "建安工程/设备采购类，审核工作台读取日报数据按月聚合"},
    {"value": "node_judge", "label": "节点判断模式", "description": "咨询/服务类，过控手动判断节点是否达成→按比例算产值"},
    {"value": "none", "label": "无产值模式", "description": "土地/招标代理/农民工专户类，不参与审核工作台，不产生产值"},
]

_LEDGER_GROUPS = [
    {"value": "construction", "label": "建安合计"},
    {"value": "equipment", "label": "设备合计"},
    {"value": "service", "label": "二类费用合计"},
    {"value": "none", "label": "不计入台账"},
]


@router.get("/contracts/review-modes")
async def list_review_modes():
    """获取审核模式列表（用于创建合同时的下拉选择）。"""
    return _REVIEW_MODES


@router.get("/contracts/ledger-groups")
async def list_ledger_groups():
    """获取台账分组列表（用于创建合同时的下拉选择）。"""
    return _LEDGER_GROUPS


@router.get("/projects/{project_id}/contracts/nos")
async def list_contract_nos(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取项目下已有合同编号列表（去重，用于创建合同时的下拉提示）。"""
    nos = await contract_service.get_contract_nos(db, project_id)
    return nos


@router.get(
    "/projects/{project_id}/payment-matrix",
    response_model=PaymentMatrixResponse,
)
async def get_payment_matrix(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取项目月度付款矩阵：按 contract_no 分组 + 节点 + 月度汇总。

    月度列头从项目 start_date/end_date 解析，支持展开/收起交互。
    """
    return await contract_service.get_payment_matrix(db, project_id)
