"""合同业务逻辑：Contract + PaymentStage + NodeTemplate CRUD"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, date, timedelta
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contract import Contract, ContractPaymentStage
from app.models.contract_payment import ContractPayment
from app.models.node_template import NodeTemplate
from app.models.project import Project
from app.schemas.contract import (
    ContractCreate,
    ContractUpdate,
    PaymentStageCreate,
    PaymentStageUpdate,
    NodesFromTemplateCreate,
    NodeTemplateCreate,
    NodeGeneratePreview,
    PaymentMatrixResponse,
    PaymentMatrixGroup,
    PaymentMatrixContract,
    PaymentMatrixNode,
)
from app.schemas.payment import (
    PaymentCreate,
    PaymentLedgerGroup,
    PaymentResponse,
)
from app.core.exceptions import NotFound, BadRequest
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
    model_dump() 自动包含 V2.2 新增字段：contract_group / review_mode / ledger_group。
    """
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
    """更新合同。

    model_dump(exclude_unset=True) 自动处理 V2.2 新增字段：contract_group / review_mode / ledger_group。
    """
    contract = await get_contract(db, contract_id)
    if not contract:
        return None

    update_data = data.model_dump(exclude_unset=True)

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

async def get_project_payment_stages(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[ContractPaymentStage]:
    """获取项目下所有合同的支付节点（跨合同汇总），按合同编号排序。"""
    result = await db.execute(
        select(ContractPaymentStage)
        .options(selectinload(ContractPaymentStage.contract))
        .join(Contract, ContractPaymentStage.contract_id == Contract.id)
        .where(
            Contract.project_id == project_id,
            Contract.deleted_at.is_(None),
        )
        .order_by(ContractPaymentStage.contract_no, ContractPaymentStage.stage_order)
    )
    return list(result.scalars().all())


async def get_payment_stages(
    db: AsyncSession,
    contract_id: uuid.UUID,
) -> list[ContractPaymentStage]:
    """获取合同的所有支付节点，按 stage_order 排序。"""
    result = await db.execute(
        select(ContractPaymentStage)
        .options(selectinload(ContractPaymentStage.contract))
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
    """手动添加支付节点。

    - stage_order 自动排列（已有最大序号 + 1）
    - agreed_amount 自动计算（合同金额 × 支付比例）
    - planned_pay_date 须 >= 合同签订日期
    """
    contract = await get_contract(db, contract_id)
    if not contract:
        raise NotFound(detail="合同不存在")

    # ── 自动计算 stage_order ──
    result = await db.execute(
        select(func.coalesce(func.max(ContractPaymentStage.stage_order), 0))
        .where(ContractPaymentStage.contract_id == contract_id)
    )
    max_order: int = result.scalar_one()
    stage_order = max_order + 1

    # ── 校验 planned_pay_date ──
    if data.planned_pay_date and contract.sign_date:
        if data.planned_pay_date < contract.sign_date:
            raise BadRequest(
                detail=f"预计支付日期({data.planned_pay_date})不能早于合同签订日期({contract.sign_date})"
            )

    # ── 自动计算 agreed_amount ──
    agreed_amount: int | None = None
    if data.agreed_ratio is not None and contract.contract_amount:
        agreed_amount = int(float(contract.contract_amount) * data.agreed_ratio)

    stage = ContractPaymentStage(
        contract_id=contract_id,
        contract_no=contract.contract_no,
        stage_order=stage_order,
        stage_name=data.stage_name,
        payment_terms=data.payment_terms,
        node_name=data.node_name,
        agreed_ratio=data.agreed_ratio,
        agreed_amount=agreed_amount,
        planned_pay_date=data.planned_pay_date,
    )
    db.add(stage)
    await db.flush()
    await db.refresh(stage)
    logger.info(f"支付节点创建成功: contract={contract_id}, stage_order={stage_order}, name={data.stage_name}")
    return stage


async def update_payment_stage(
    db: AsyncSession,
    stage_id: uuid.UUID,
    data: PaymentStageUpdate,
) -> ContractPaymentStage | None:
    """更新支付节点。

    - 修改 agreed_ratio 时自动重算 agreed_amount
    - planned_pay_date 须 >= 合同签订日期
    """
    stage = await get_payment_stage(db, stage_id)
    if not stage:
        return None

    update_data = data.model_dump(exclude_unset=True)

    # ── 自动重算 agreed_amount ──
    if "agreed_ratio" in update_data:
        contract = await get_contract(db, stage.contract_id)
        if contract and contract.contract_amount and update_data["agreed_ratio"] is not None:
            update_data["agreed_amount"] = int(float(contract.contract_amount) * update_data["agreed_ratio"])

    # ── 校验 planned_pay_date ──
    if "planned_pay_date" in update_data:
        planned_date = update_data["planned_pay_date"]
        if planned_date is not None:
            contract = await get_contract(db, stage.contract_id)
            if contract and contract.sign_date and planned_date < contract.sign_date:
                raise BadRequest(
                    detail=f"预计支付日期({planned_date})不能早于合同签订日期({contract.sign_date})"
                )

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
    """标记支付节点完成/取消完成（切换 is_completed）。

    标记完成时同时设置 triggered_at 为当天（node_judge 模式下用于防重复计费）。
    取消完成时清空 triggered_at。
    """
    stage = await get_payment_stage(db, stage_id)
    if not stage:
        return None

    stage.is_completed = not stage.is_completed
    if stage.is_completed:
        stage.completed_at = datetime.now(UTC)
        stage.triggered_at = date.today()
    else:
        stage.completed_at = None
        stage.triggered_at = None
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


# ═══════════════════════════════════════════════════════════════════
# 合同分组 (V2.2)
# ═══════════════════════════════════════════════════════════════════

async def get_contract_groups(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[dict]:
    """按 contract_group 分组返回合同列表。"""
    result = await db.execute(
        select(Contract)
        .where(
            Contract.project_id == project_id,
            Contract.deleted_at.is_(None),
        )
        .order_by(Contract.contract_group, Contract.contract_no)
    )
    contracts = list(result.scalars().all())

    groups: dict[str, list[Contract]] = {}
    for c in contracts:
        group = c.contract_group or "__ungrouped__"
        if group not in groups:
            groups[group] = []
        groups[group].append(c)

    return [
        {"contract_group": group, "contracts": items}
        for group, items in groups.items()
    ]


async def get_contract_nos(db: AsyncSession, project_id: uuid.UUID) -> list[str]:
    """获取项目下所有去重合同编号（用于创建合同时的 AutoComplete 提示）。"""
    result = await db.execute(
        select(Contract.contract_no)
        .where(
            Contract.project_id == project_id,
            Contract.deleted_at.is_(None),
        )
        .distinct()
        .order_by(Contract.contract_no)
    )
    return [row[0] for row in result.all()]


# ═══════════════════════════════════════════════════════════════════
# 月度付款矩阵 (V2.2)
# ═══════════════════════════════════════════════════════════════════

def _parse_month_range(start_date: date | None, end_date: date | None) -> list[str]:
    """从 start_date/end_date 解析月份列表。

    如 start=2025-12-01, end=2027-11-01 → ['2025-12', '2026-01', ..., '2027-11']
    """
    if not start_date or not end_date:
        return []
    months: list[str] = []
    cur = date(start_date.year, start_date.month, 1)
    end = date(end_date.year, end_date.month, 1)
    while cur <= end:
        months.append(cur.strftime("%Y-%m"))
        cur += relativedelta(months=1)
    return months


async def get_payment_matrix(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> PaymentMatrixResponse:
    """获取项目月度付款矩阵：按 contract_no 分组 + 节点 + 月度汇总。

    先查项目获取 start_date/end_date 和名称，再批量加载合同+节点。
    """
    # ── 1. 获取项目 ──
    proj_result = await db.execute(select(Project).where(Project.id == project_id, Project.deleted_at.is_(None)))
    project = proj_result.scalar_one_or_none()
    if project is None:
        raise NotFound(detail="项目不存在")

    month_range = _parse_month_range(project.start_date, project.end_date)

    # ── 容错：start_date/end_date 为空时默认 24 个月（从创建时间起） ──
    if not month_range:
        from dateutil.relativedelta import relativedelta
        start = date(project.created_at.year, project.created_at.month, 1)
        end = start + relativedelta(months=23)
        cur = start
        while cur <= end:
            month_range.append(cur.strftime("%Y-%m"))
            cur += relativedelta(months=1)

    # ── 2. 批量加载合同 + 节点 ──
    ct_result = await db.execute(
        select(Contract)
        .where(Contract.project_id == project_id, Contract.deleted_at.is_(None))
        .options(selectinload(Contract.payment_stages))
        .order_by(Contract.contract_no, Contract.seq)
    )
    contracts: list[Contract] = list(ct_result.scalars().all())

    # ── 3. 按 contract_no 分组 ──
    groups_map: dict[str, list[Contract]] = {}
    for c in contracts:
        no = c.contract_no
        groups_map.setdefault(no, []).append(c)

    groups: list[PaymentMatrixGroup] = []
    monthly_totals: dict[str, float] = {m: 0.0 for m in month_range}

    for contract_no, ct_list in groups_map.items():
        group_total = 0
        matrix_contracts: list[PaymentMatrixContract] = []

        for ct in ct_list:
            nodes: list[PaymentMatrixNode] = []
            for st in ct.payment_stages:
                if st.agreed_ratio and st.agreed_ratio > 0:
                    node = PaymentMatrixNode(
                        node_name=st.node_name,
                        stage_name=st.stage_name,
                        agreed_amount=st.agreed_amount,
                        agreed_ratio=st.agreed_ratio,
                        planned_pay_date=st.planned_pay_date,
                        is_completed=st.is_completed,
                    )
                    nodes.append(node)

                    # ── 累加入月度汇总 ──
                    if st.planned_pay_date and st.agreed_amount:
                        month_key = st.planned_pay_date.strftime("%Y-%m")
                        if month_key in monthly_totals:
                            monthly_totals[month_key] += st.agreed_amount / 100.0

            mc = PaymentMatrixContract(
                contract_id=ct.id,
                supplier_name=ct.supplier_name,
                contract_desc=ct.contract_desc,
                contract_amount=ct.contract_amount,
                sign_date=ct.sign_date,
                review_mode=ct.review_mode,
                nodes=nodes,
            )
            matrix_contracts.append(mc)
            group_total += ct.contract_amount or 0

        groups.append(PaymentMatrixGroup(
            contract_no=contract_no,
            total_amount=group_total,
            contracts=matrix_contracts,
        ))

    return PaymentMatrixResponse(
        project_name=project.project_name,
        month_range=month_range,
        monthly_totals=monthly_totals,
        groups=groups,
    )


# ═══════════════════════════════════════════════════════════════════
# 支付台账 (V2.2)
# ═══════════════════════════════════════════════════════════════════


def _payment_to_response(payment: ContractPayment) -> PaymentResponse:
    """将 ContractPayment ORM 转为 PaymentResponse，填充关联字段。"""
    resp = PaymentResponse.model_validate(payment)
    # 填充 stage_name
    if payment.stage:
        resp.stage_name = payment.stage.stage_name
    # 填充 supplier_name
    if payment.contract:
        resp.supplier_name = payment.contract.supplier_name
    return resp


async def get_contract_payments(
    db: AsyncSession,
    contract_id: uuid.UUID,
    year: int | None = None,
) -> list[ContractPayment]:
    """获取合同支付记录，按 confirmed_at 月份分组返回（可选按年份筛选）。"""
    stmt = (
        select(ContractPayment)
        .options(selectinload(ContractPayment.stage), selectinload(ContractPayment.contract))
        .where(ContractPayment.contract_id == contract_id)
        .order_by(ContractPayment.confirmed_at.desc().nullslast(), ContractPayment.created_at.desc())
    )
    if year is not None:
        stmt = stmt.where(func.extract("year", ContractPayment.confirmed_at) == year)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_payment(
    db: AsyncSession,
    contract_id: uuid.UUID,
    data: PaymentCreate,
) -> ContractPayment:
    """创建支付记录（报送）。

    逻辑：
    1. 查 stage → 拿 agreed_amount
    2. 查该 stage 的所有 confirmed 付款 → 求已批累计
    3. approved_amount = min(agreed_amount - 已批累计, reported_amount)
    4. status = 'pending', 写入 DB
    """
    # ── 查支付节点 ──
    stage = await get_payment_stage(db, data.stage_id)
    if not stage:
        raise NotFound(detail="支付节点不存在")

    # ── 查合同 ──
    contract = await get_contract(db, contract_id)
    if not contract:
        raise NotFound(detail="关联合同不存在")

    # ── 查该 stage 已批累计 ──
    result = await db.execute(
        select(func.coalesce(func.sum(ContractPayment.approved_amount), 0))
        .where(
            ContractPayment.stage_id == data.stage_id,
            ContractPayment.status == "confirmed",
        )
    )
    already_approved: int = result.scalar_one()

    # ── 计算批准金额 ──
    agreed_amount = stage.agreed_amount or 0
    approved_amount = min(agreed_amount - already_approved, data.reported_amount)
    if approved_amount < 0:
        approved_amount = 0

    payment = ContractPayment(
        contract_id=contract.id,
        contract_no=contract.contract_no,
        stage_id=data.stage_id,
        reported_amount=data.reported_amount,
        approved_amount=approved_amount,
        ledger_group=contract.ledger_group or "service",
        status="pending",
    )
    db.add(payment)
    await db.flush()
    await db.refresh(payment)

    logger.info(
        f"支付记录创建成功: contract={contract.contract_no}, "
        f"stage={data.stage_id}, reported={data.reported_amount}, "
        f"approved={approved_amount}"
    )
    return payment


async def get_payments(
    db: AsyncSession,
    contract_id: uuid.UUID | None = None,
    stage_id: uuid.UUID | None = None,
    status_filter: str | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[PaymentResponse], int]:
    """分页查询支付记录。"""
    stmt = (
        select(ContractPayment)
        .options(selectinload(ContractPayment.stage), selectinload(ContractPayment.contract))
        .order_by(ContractPayment.created_at.desc())
    )
    count_stmt = select(func.count(ContractPayment.id))

    if contract_id:
        stmt = stmt.where(ContractPayment.contract_id == contract_id)
        count_stmt = count_stmt.where(ContractPayment.contract_id == contract_id)

    if stage_id:
        stmt = stmt.where(ContractPayment.stage_id == stage_id)
        count_stmt = count_stmt.where(ContractPayment.stage_id == stage_id)

    if status_filter:
        stmt = stmt.where(ContractPayment.status == status_filter)
        count_stmt = count_stmt.where(ContractPayment.status == status_filter)

    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(ContractPayment.contract_no.ilike(like))
        count_stmt = count_stmt.where(ContractPayment.contract_no.ilike(like))

    items, total = await paginate(db, stmt, page=page, page_size=page_size, model=ContractPayment, count_stmt=count_stmt)
    return [_payment_to_response(p) for p in items], total


async def get_monthly_payment_summary(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[PaymentLedgerGroup]:
    """支付台账按月分组汇总。

    查项目下所有支付记录，按 created_at 的月份分组。
    """
    from collections import defaultdict

    result = await db.execute(
        select(ContractPayment)
        .options(selectinload(ContractPayment.stage), selectinload(ContractPayment.contract))
        .join(Contract, ContractPayment.contract_id == Contract.id)
        .where(
            Contract.project_id == project_id,
            Contract.deleted_at.is_(None),
        )
        .order_by(ContractPayment.created_at.desc())
    )
    payments: list[ContractPayment] = list(result.scalars().all())

    # 按月份分组
    groups_map: dict[str, list[ContractPayment]] = defaultdict(list)
    for p in payments:
        month_key = p.created_at.strftime("%Y-%m")
        groups_map[month_key].append(p)

    groups: list[PaymentLedgerGroup] = []
    for month in sorted(groups_map.keys(), reverse=True):
        items = groups_map[month]
        groups.append(PaymentLedgerGroup(
            month=month,
            items=[_payment_to_response(p) for p in items],
            month_total_reported=sum(p.reported_amount for p in items),
            month_total_approved=sum(p.approved_amount for p in items),
        ))

    return groups


async def confirm_payment(
    db: AsyncSession,
    payment_id: uuid.UUID,
) -> ContractPayment:
    """确认批准支付。

    状态校验：只有 pending 状态的支付记录可以确认。
    """
    result = await db.execute(
        select(ContractPayment)
        .options(selectinload(ContractPayment.stage), selectinload(ContractPayment.contract))
        .where(ContractPayment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise NotFound(detail="支付记录不存在")

    if payment.status != "pending":
        raise BadRequest(
            detail=f"当前状态为 {payment.status}，只有 pending 状态的支付记录可以确认"
        )

    payment.status = "confirmed"
    payment.confirmed_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(payment)

    logger.info(f"支付已确认: id={payment_id}, amount={payment.approved_amount}")
    return payment


async def reject_payment(
    db: AsyncSession,
    payment_id: uuid.UUID,
    reason: str,
) -> ContractPayment:
    """驳回支付。

    状态校验：只有 pending 状态的支付记录可以驳回。
    """
    result = await db.execute(
        select(ContractPayment)
        .options(selectinload(ContractPayment.stage), selectinload(ContractPayment.contract))
        .where(ContractPayment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise NotFound(detail="支付记录不存在")

    if payment.status != "pending":
        raise BadRequest(
            detail=f"当前状态为 {payment.status}，只有 pending 状态的支付记录可以驳回"
        )

    payment.status = "rejected"
    payment.reject_reason = reason
    payment.confirmed_at = None

    await db.flush()
    await db.refresh(payment)

    logger.info(f"支付已驳回: id={payment_id}, reason={reason}")
    return payment
