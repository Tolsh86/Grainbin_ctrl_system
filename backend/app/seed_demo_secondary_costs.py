"""创建二类费用演示数据。

执行：
    python -m app.seed_demo_secondary_costs
预演：
    python -m app.seed_demo_secondary_costs --dry-run

数据结构来自《合同支付情况汇总表》：仅创建项目、二类费用合同和合同支付节点，
不创建审核记录、月度台账或支付记录。合同金额为用于展示的固定演示金额。
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.contract import Contract, ContractPaymentStage
from app.models.project import Project


PROJECT_CODE = "XTH-DEMO-SECONDARY-2026"
PROJECT_NAME = "川西现代粮食物流中心建设项目"


@dataclass(frozen=True)
class Stage:
    name: str
    ratio: str
    terms: str


@dataclass(frozen=True)
class DemoContract:
    code: str
    supplier: str
    description: str
    sign_date: date | None
    amount_yuan: str
    stages: tuple[Stage, ...]


def stages(*items: tuple[str, str, str]) -> tuple[Stage, ...]:
    return tuple(Stage(*item) for item in items)


# 金额均为固定演示金额（元），保留真实台账常见的非整百/非整千两位小数形态。
CONTRACTS: tuple[DemoContract, ...] = (
    DemoContract("CX001", "四川锦鑫川荣工程咨询有限公司", "四川省国家工程投资建设委托招标代理", date(2024, 8, 19), "187361.12", stages(
        ("招标代理服务", "1.00", "完成合同约定代理事项并完整移交招标档案资料后 10 个工作日内一次性支付。"),
    )),
    DemoContract("CX002", "重庆大正建设工程经济技术有限公司", "四川省国家工程投资建设委托招标代理", date(2024, 8, 19), "216480.50", stages(
        ("招标代理服务", "1.00", "完成代理事项、移交招标档案资料后一次性支付。"),
    )),
    DemoContract("CX003", "中资锐诚工程项目管理有限公司", "可研评审服务合同", date(2025, 5, 14), "156800.00", stages(
        ("成果交付", "1.00", "完成可研评审服务成果交付后一次性支付。"),
    )),
    DemoContract("CX004", "德阳市罗江区自然资源和规划局", "国有建设用地使用权出让合同", date(2025, 8, 4), "1286431.75", stages(
        ("土地出让", "1.00", "完成国有建设用地使用权出让相关手续后支付。"),
    )),
    DemoContract("CX005", "中储粮成都储藏研究院有限公司", "建设工程勘察、初设设计服务合同", date(2025, 8, 11), "2173916.68", stages(
        ("合同签订 / 预付款", "0.20", "合同签订后 30 日内，支付合同暂定设计价的 20%。"),
        ("方案设计审批", "0.30", "提交方案设计资料并经主管部门审批通过后，支付至合同金额的 50%。"),
        ("初设评审", "0.30", "初步设计通过评审并取得概算审核批复后，支付至合同金额的 80%。"),
        ("竣工结算", "0.20", "项目竣工并完成财评审核后支付剩余尾款。"),
    )),
    DemoContract("CX006", "四川都林工程咨询有限公司", "建设工程造价咨询合同", date(2025, 8, 18), "438705.36", stages(
        ("成果文件交付", "1.00", "提交完整成果文件后 20 个工作日内一次性付清。"),
    )),
    DemoContract("CX007", "四川卓立建设工程咨询有限公司", "建设工程施工图设计文件审查合同", date(2025, 11, 20), "289640.80", stages(
        ("审查报告交付", "1.00", "施工图设计文件审查完成并交付审查报告后支付。"),
    )),
    DemoContract("CX009", "中凯俊成建设咨询有限公司", "全过程咨询（监理、造价、结算）", date(2025, 11, 27), "3040740.00", stages(
        ("合同签订", "0.10", "合同签订后支付监理及全过程咨询服务费的 10%。"),
        ("施工图审查 / 产值达标", "0.20", "施工图审查完成或工程产值达到约定比例后，支付至合同金额的 30%。"),
        ("竣工验收", "0.40", "工程竣工验收合格后，支付至合同金额的 70%。"),
        ("结算与决算", "0.30", "项目结算审核及财务决算完成后支付剩余款项。"),
    )),
    DemoContract("CX010", "德阳城发清源生态环境咨询服务有限公司", "项目管理咨询服务合同", date(2025, 12, 17), "1283496.20", stages(
        ("合同签订", "0.30", "合同签订后支付合同金额的 30% 作为预付款。"),
        ("招投标完成", "0.20", "完成设计、施工、监理招投标并签订合同后，支付至合同金额的 50%。"),
        ("竣工结算", "0.45", "竣工验收合格及施工项目结算审核后，支付至合同金额的 95%。"),
        ("缺陷责任期", "0.05", "缺陷责任期满后支付至合同金额的 100%。"),
    )),
    DemoContract("CX011", "德阳城发清源生态环境咨询服务有限公司", "水土保持方案编制和验收咨询服务", date(2026, 1, 14), "786325.64", stages(
        ("合同签订", "0.30", "合同签订后 30 个工作日内支付水土保持方案编制服务费的 30%。"),
        ("方案成果验收", "0.30", "提交经验收的编制成果后，支付至方案编制服务费的 60%。"),
        ("备案验收", "0.40", "完成水土保持设施竣工验收并备案后支付剩余款项。"),
    )),
    DemoContract("CX012", "四川鑫科锐工程勘察设计有限公司", "测绘服务合同", date(2026, 1, 14), "532761.20", stages(
        ("合同签订", "0.30", "合同签订后支付合同金额的 30% 作为预付款。"),
        ("成果验收", "0.30", "测绘成果验收合格后支付至合同金额的 60%。"),
        ("主管部门批复", "0.40", "取得项目所在地主管部门批复后支付剩余合同金额。"),
    )),
    DemoContract("CX014", "四川创安太平科技有限公司", "安全技术服务合同", date(2026, 1, 27), "187361.12", stages(
        ("成果验收", "1.00", "完成安全条件和设施分析成果文件并验收、提交付款资料后一次性支付。"),
    )),
    DemoContract("CX015", "河南工大设计研究院有限公司", "信息化咨询服务", date(2026, 1, 29), "92800.00", stages(
        ("合同生效", "0.30", "合同生效后 30 日内支付咨询费用总价的 30%。"),
        ("报告成果交付", "0.40", "提交全部信息化建设报告成果后支付咨询费用总价的 40%。"),
        ("验收合格", "0.30", "委托方验收合格后支付剩余咨询费用。"),
    )),
    DemoContract("CX016", "四川西南科正建设工程质量检测有限公司", "工程检测服务", date(2026, 2, 3), "564389.36", stages(
        ("合同签订", "0.30", "合同签订后支付合同金额的 30%。"),
        ("检测报告交付", "0.50", "完成检测工作并提交完整检测报告后，支付至核定检测费的 80%。"),
        ("结算审核", "0.20", "项目结算审核完成后支付剩余尾款。"),
    )),
    DemoContract("CX017", "四川沁合勘察测绘有限公司", "地下管网探测服务", date(2026, 3, 17), "176842.50", stages(
        ("服务完成", "1.00", "具备合同约定服务费用支付条件后 20 个工作日内一次性支付。"),
    )),
    DemoContract("CX018", "析谱科技（成都）有限公司", "职业病危害评价服务", date(2026, 3, 27), "318560.40", stages(
        ("预评价成果", "0.30", "预评价提交成果文件或取得备案回执后支付 30%。"),
        ("防护设施设计", "0.30", "防护设施设计专篇提交成果文件或取得备案回执后支付 30%。"),
        ("控制效果评价", "0.40", "控制效果评价提交成果并移交全部资料后支付 40%。"),
    )),
)


def yuan_to_fen(amount: str) -> int:
    return int(Decimal(amount) * 100)


def ensure_project(session: Session, dry_run: bool) -> tuple[Project | None, bool]:
    project = session.execute(select(Project).where(Project.project_code == PROJECT_CODE)).scalar_one_or_none()
    if project:
        return project, False
    if dry_run:
        return None, True

    project = Project(
        project_name=PROJECT_NAME,
        project_code=PROJECT_CODE,
        project_nature="功能性项目",
        invest_timing="续投项目",
        invest_nature="固定资产投资",
        region="市内",
        owner_unit="四川德阳省食油储备库",
        responsible_unit="兴天华过控项目组",
        construction_content="粮食物流中心建设配套二类费用合同演示数据。",
        start_date=date(2025, 12, 1),
        end_date=date(2027, 11, 30),
        planned_total_invest=19_320_330_000,
        planned_invest_2026=7_500_000_000,
        project_status="constructing",
    )
    session.add(project)
    session.flush()
    return project, True


def seed_contract(session: Session, project: Project, spec: DemoContract, seq: int, dry_run: bool) -> tuple[bool, int]:
    contract = session.execute(
        select(Contract).where(Contract.project_id == project.id, Contract.contract_no == spec.code, Contract.deleted_at.is_(None))
    ).scalar_one_or_none()
    created = contract is None
    if contract is None:
        if dry_run:
            return True, len(spec.stages)
        contract = Contract(
            project_id=project.id,
            seq=seq,
            contract_no=spec.code,
            supplier_name=spec.supplier,
            contract_desc=spec.description,
            sign_date=spec.sign_date,
            contract_amount=yuan_to_fen(spec.amount_yuan),
            contract_type="secondary",
            status="active",
            contract_group=spec.code,
            review_mode="node_judge",
            ledger_group="service",
        )
        session.add(contract)
        session.flush()

    existing_orders = set(session.execute(
        select(ContractPaymentStage.stage_order).where(ContractPaymentStage.contract_id == contract.id)
    ).scalars())
    created_stages = 0
    for order, stage in enumerate(spec.stages, 1):
        if order in existing_orders:
            continue
        if not dry_run:
            ratio = Decimal(stage.ratio)
            session.add(ContractPaymentStage(
                contract_id=contract.id,
                contract_no=contract.contract_no,
                stage_order=order,
                stage_name=stage.name,
                node_name=stage.name,
                payment_terms=stage.terms,
                agreed_ratio=ratio,
                agreed_amount=int(Decimal(contract.contract_amount or 0) * ratio),
            ))
        created_stages += 1
    return created, created_stages


def seed(dry_run: bool = False) -> None:
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    with Session(engine) as session:
        project, project_created = ensure_project(session, dry_run)
        created_contracts = 0
        created_stages = 0
        if project is None:
            created_contracts = len(CONTRACTS)
            created_stages = sum(len(item.stages) for item in CONTRACTS)
        else:
            next_seq = (session.execute(
                select(func.coalesce(func.max(Contract.seq), 0)).where(Contract.project_id == project.id)
            ).scalar_one() or 0) + 1
            for index, spec in enumerate(CONTRACTS):
                contract_created, stage_count = seed_contract(session, project, spec, next_seq + index, dry_run=dry_run)
                created_contracts += int(contract_created)
                created_stages += stage_count
            if not dry_run:
                session.commit()

    action = "预演" if dry_run else "已写入"
    print(f"{action}：项目 {'新建' if project_created else '已存在'}，新增合同 {created_contracts} 份，新增支付节点 {created_stages} 个。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="创建二类费用演示项目、合同和支付节点")
    parser.add_argument("--dry-run", action="store_true", help="只输出将创建的数据统计，不写入数据库")
    seed(dry_run=parser.parse_args().dry_run)
