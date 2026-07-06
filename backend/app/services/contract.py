"""合同业务逻辑：Contract + PaymentStage + NodeTemplate CRUD"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, date, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contract, ContractPaymentStage
from app.models.node_template import NodeTemplate
from app.schemas.contract import (
    ContractCreate,
    ContractUpdate,
    PaymentStageCreate,
    PaymentStageUpdate,
    NodesFromTemplateCreate,
    NodeTemplateCreate,
    NodeGeneratePreview,
)
from app.core.exceptions import NotFound, BadRequest, Conflict
from app.utils.db import paginate, active_filter


# ═══════════════════════════════════════════════════════════════════
# 合同 CRUD
# ═══════════════════════════════════════════════════════════════════

async def get_contracts(
    db: AsyncSession,
    project_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
    contract_type: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
) -> tuple[list[Contract], int]:
    """分页查询合同列表，支持按项目、类型、状态、关键词筛选。"""
    stmt = select(Contract).order_by(Contract.created_at.desc())
    count_stmt = select(func.count(Contract.id))

    if project_id:
        stmt = stmt.where(Contract.project_id == project_id)
        count_stmt = count_stmt.where(Contract.project_id == project_id)
    if contract_type:
        stmt = stmt.where(Contract.contract_type == contract_type)
        count_stmt = count_stmt.where(Contract.contract_type == contract_type)
    if status:
        stmt = stmt.where(Contract.status == status)
        count_stmt = count_stmt.where(Contract.status == status)
    if keyword:
        like = f"%{keyword}%"
        cond = Contract.contract_no.ilike(like) | Contract.supplier_name.ilike(like) | Contract.contract_desc.ilike(like)
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)

    return await paginate(db, stmt, page=page, page_size=page_size, model=Contract, count_stmt=count_stmt)


async def get_contract(db: AsyncSession, contract_id: uuid.UUID) -> Contract | None:
    """按 ID 获取合同。"""
    result = await db.execute(
        active_filter(select(Contract).where(Contract.id == contract_id), Contract)
    )
    return result.scalar_one_or_none()


async def get_contract_detail(db: AsyncSession, contract_id: uuid.UUID) -> Contract | None:
    """获取合同详情（含支付节点）。"""
    result = await db.execute(
        active_filter(select(Contract).where(Contract.id == contract_id), Contract)
    )
    return result.scalar_one_or_none()


async def get_next_seq(db: AsyncSession, project_id: uuid.UUID) -> int:
    """获取项目下下一个合同序号。"""
    result = await db.execute(
        select(func.coalesce(func.max(Contract.seq), 0)).where(Contract.project_id == project_id)
    )
    return (result.scalar_one() or 0) + 1


async def create_contract(db: AsyncSession, project_id: uuid.UUID, data: ContractCreate) -> Contract:
    """创建合同。

    自动分配 seq，检查 contract_no 唯一性。
    """
    # 检查编号唯一性
    existing = await db.execute(
        active_filter(select(Contract).where(Contract.contract_no == data.contract_no), Contract)
    )
    if existing.scalar_one_or_none():
        raise Conflict(detail=f"合同编号 '{data.contract_no}' 已存在")

    seq = await get_next_seq(db, project_id)
    contract = Contract(
        project_id=project_id,
        seq=seq,
        **data.model_dump(),
    )
    db.add(contract)
    await db.flush()
    await db.refresh(contract)
    logger.info(f"合同创建成功: project={project_id}, contract_no={data.contract_no}")
    return contract


async def update_contract(db: AsyncSession, contract_id: uuid.UUID, data: ContractUpdate) -> Contract | None:
    """更新合同。"""
    contract = await get_contract(db, contract_id)
    if not contract:
        return None

    update_data = data.model_dump(exclude_unset=True)

    # 检查 contract_no 唯一性（如果修改了）
    if "contract_no" in update_data and update_data["contract_no"] != contract.contract_no:
        existing = await db.execute(
            active_filter(
                select(Contract).where(Contract.contract_no == update_data["contract_no"], Contract.id != contract_id),
                Contract,
            )
        )
        if existing.scalar_one_or_none():
            raise Conflict(detail=f"合同编号 '{update_data['contract_no']}' 已被占用")

    for key, value in update_data.items():
        setattr(contract, key, value)
    await db.flush()
    await db.refresh(contract)
    logger.info(f"合同更新成功: id={contract_id}, no={contract.contract_no}")
    return contract


async def delete_contract(db: AsyncSession, contract_id: uuid.UUID) -> bool:
    """软删除合同。"""
    contract = await get_contract(db, contract_id)
    if not contract:
        return False
    contract.deleted_at = datetime.now(UTC)
    await db.flush()
    logger.info(f"合同已删除: id={contract_id}, no={contract.contract_no}")
    return True


# ═══════════════════════════════════════════════════════════════════
# 支付节点 CRUD
# ═══════════════════════════════════════════════════════════════════

async def get_payment_stages(
    db: AsyncSession,
    contract_id: uuid.UUID,
) -> list[ContractPaymentStage]:
    """获取合同的所有支付节点，按 stage_order 排序。"""
    result = await db.execute(
        select(ContractPaymentStage)
        .where(ContractPaymentStage.contract_id == contract_id)
        .order_by(ContractPaymentStage.stage_order)
    )
    return list(result.scalars().all())


async def get_payment_stage(db: AsyncSession, stage_id: uuid.UUID) -> ContractPaymentStage | None:
    """按 ID 获取支付节点。"""
    result = await db.execute(
        select(ContractPaymentStage).where(ContractPaymentStage.id == stage_id)
    )
    return result.scalar_one_or_none()


async def create_payment_stage(
    db: AsyncSession,
    contract_id: uuid.UUID,
    data: PaymentStageCreate,
) -> ContractPaymentStage:
    """手动添加支付节点。"""
    # 获取合同以获取 contract_no
    contract = await get_contract(db, contract_id)
    if not contract:
        raise NotFound(detail="合同不存在")

    stage = ContractPaymentStage(
        contract_id=contract_id,
        contract_no=contract.contract_no,
        **data.model_dump(),
    )
    db.add(stage)
    await db.flush()
    await db.refresh(stage)
    logger.info(f"支付节点创建成功: contract={contract_id}, stage_order={data.stage_order}, name={data.stage_name}")
    return stage


async def update_payment_stage(
    db: AsyncSession,
    stage_id: uuid.UUID,
    data: PaymentStageUpdate,
) -> ContractPaymentStage | None:
    """更新支付节点。"""
    stage = await get_payment_stage(db, stage_id)
    if not stage:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(stage, key, value)
    await db.flush()
    await db.refresh(stage)
    return stage


async def delete_payment_stage(db: AsyncSession, stage_id: uuid.UUID) -> bool:
    """删除支付节点（硬删除，因为 PaymentStage 没有软删除字段）。"""
    stage = await get_payment_stage(db, stage_id)
    if not stage:
        return False
    await db.delete(stage)
    await db.flush()
    return True


async def complete_payment_stage(db: AsyncSession, stage_id: uuid.UUID) -> ContractPaymentStage | None:
    """标记支付节点完成/取消完成（切换 is_completed）。"""
    stage = await get_payment_stage(db, stage_id)
    if not stage:
        return None

    stage.is_completed = not stage.is_completed
    stage.completed_at = datetime.now(UTC) if stage.is_completed else None
    await db.flush()
    await db.refresh(stage)
    return stage


async def generate_nodes_from_template(
    db: AsyncSession,
    contract_id: uuid.UUID,
    data: NodesFromTemplateCreate,
) -> list[ContractPaymentStage]:
    """从模板生成支付节点。

    1. 检查合同是否存在
    2. 检查合同是否已有节点（防止重复生成）
    3. 读取模板配置
    4. 批量创建 PaymentStage
    """
    contract = await get_contract(db, contract_id)
    if not contract:
        raise NotFound(detail="合同不存在")

    # 检查是否已有节点
    existing = await db.execute(
        select(ContractPaymentStage).where(
            ContractPaymentStage.contract_id == contract_id,
            ContractPaymentStage.stage_order != 0,  # 排除汇总行
        ).limit(1)
    )
    if existing.scalar_one_or_none():
        raise BadRequest(detail="该合同已有支付节点，不能重复生成。如需重新生成请先删除现有节点")

    # 获取模板
    result = await db.execute(
        select(NodeTemplate).where(NodeTemplate.id == data.template_id, NodeTemplate.deleted_at.is_(None))
    )
    template = result.scalar_one_or_none()
    if not template:
        raise NotFound(detail="节点模板不存在")

    # 解析模板 stages
    stages_data = template.stages
    if isinstance(stages_data, dict):
        stages_list = stages_data.get("stages", [])
    elif isinstance(stages_data, list):
        stages_list = stages_data
    else:
        raise BadRequest(detail="模板数据格式无效")

    if not stages_list:
        raise BadRequest(detail="模板中没有节点配置")

    created_stages: list[ContractPaymentStage] = []
    for cfg in stages_list:
        stage_order = cfg.get("order", 0)
        node_name = cfg.get("node_name", "")
        agreed_ratio = Decimal(str(cfg.get("agreed_ratio", 0)))
        trigger_condition = cfg.get("trigger_condition", "")
        offset_days = cfg.get("offset_days", 0)

        # 计算 agreed_amount
        contract_amount = Decimal(str(data.contract_amount))
        agreed_amount = int(contract_amount * agreed_ratio) if data.contract_amount else None

        # 计算 planned_pay_date
        planned_pay_date = None
        if data.sign_date and offset_days:
            planned_pay_date = data.sign_date + timedelta(days=int(offset_days))

        # 根据 order 推断 stage_name
        stage_name_map = {1: "施工前阶段", 2: "施工中阶段", 3: "竣工阶段", 4: "结算后阶段", 5: "质保尾款阶段", 0: "汇总"}
        stage_name = stage_name_map.get(stage_order, f"阶段{stage_order}")

        stage = ContractPaymentStage(
            contract_id=contract_id,
            contract_no=contract.contract_no,
            stage_order=stage_order,
            stage_name=stage_name,
            payment_terms=trigger_condition,
            node_name=node_name,
            agreed_ratio=float(agreed_ratio),
            agreed_amount=agreed_amount,
            planned_pay_date=planned_pay_date,
        )
        db.add(stage)
        created_stages.append(stage)

    await db.flush()
    for s in created_stages:
        await db.refresh(s)

    logger.info(
        f"从模板生成支付节点: contract={contract_id}, template={data.template_id}, "
        f"nodes={len(created_stages)}"
    )
    return created_stages


async def preview_nodes_from_template(
    db: AsyncSession,
    template_id: uuid.UUID,
    data: NodesFromTemplateCreate,
) -> list[NodeGeneratePreview]:
    """预览从模板生成节点的结果（不写入数据库）。"""
    result = await db.execute(
        select(NodeTemplate).where(NodeTemplate.id == template_id, NodeTemplate.deleted_at.is_(None))
    )
    template = result.scalar_one_or_none()
    if not template:
        raise NotFound(detail="节点模板不存在")

    stages_data = template.stages
    if isinstance(stages_data, dict):
        stages_list = stages_data.get("stages", [])
    elif isinstance(stages_data, list):
        stages_list = stages_data
    else:
        raise BadRequest(detail="模板数据格式无效")

    previews: list[NodeGeneratePreview] = []
    contract_amount = Decimal(str(data.contract_amount))

    for cfg in stages_list:
        order = cfg.get("order", 0)
        node_name = cfg.get("node_name", "")
        agreed_ratio = float(cfg.get("agreed_ratio", 0))
        offset_days = cfg.get("offset_days", 0)
        trigger_condition = cfg.get("trigger_condition", "")

        agreed_amount = int(contract_amount * Decimal(str(agreed_ratio)))
        planned_pay_date = None
        if data.sign_date and offset_days:
            planned_pay_date = data.sign_date + timedelta(days=int(offset_days))

        stage_name_map = {1: "施工前阶段", 2: "施工中阶段", 3: "竣工阶段", 4: "结算后阶段", 5: "质保尾款阶段", 0: "汇总"}
        stage_name = stage_name_map.get(order, f"阶段{order}")

        previews.append(NodeGeneratePreview(
            stage_order=order,
            stage_name=stage_name,
            node_name=node_name,
            agreed_ratio=agreed_ratio,
            agreed_amount=agreed_amount,
            planned_pay_date=planned_pay_date,
            trigger_condition=trigger_condition,
        ))

    return previews


# ═══════════════════════════════════════════════════════════════════
# 节点模板 CRUD
# ═══════════════════════════════════════════════════════════════════

async def get_node_templates(
    db: AsyncSession,
    biz_type: str | None = None,
    is_preset: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[NodeTemplate], int]:
    """分页查询节点模板。"""
    stmt = select(NodeTemplate).order_by(NodeTemplate.created_at.desc())
    count_stmt = select(func.count(NodeTemplate.id))

    if biz_type:
        stmt = stmt.where(NodeTemplate.biz_type == biz_type)
        count_stmt = count_stmt.where(NodeTemplate.biz_type == biz_type)
    if is_preset is not None:
        stmt = stmt.where(NodeTemplate.is_preset.is_(is_preset))
        count_stmt = count_stmt.where(NodeTemplate.is_preset.is_(is_preset))

    return await paginate(db, stmt, page=page, page_size=page_size, model=NodeTemplate, count_stmt=count_stmt)


async def get_node_template(db: AsyncSession, template_id: uuid.UUID) -> NodeTemplate | None:
    """按 ID 获取节点模板。"""
    result = await db.execute(
        active_filter(select(NodeTemplate).where(NodeTemplate.id == template_id), NodeTemplate)
    )
    return result.scalar_one_or_none()


async def create_node_template(db: AsyncSession, data: NodeTemplateCreate) -> NodeTemplate:
    """创建用户自定义节点模板。"""
    template = NodeTemplate(
        template_name=data.template_name,
        biz_type=data.biz_type,
        description=data.description,
        is_preset=False,
        stages={"stages": data.stages},
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return template
