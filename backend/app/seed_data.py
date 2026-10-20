"""种子数据脚本：预置 18 家供应商 + 3 套节点模板

运行方式：
  python -m app.seed_data

或通过 Alembic 迁移调用：
  from app.seed_data import seed_dict_suppliers, seed_node_templates
"""

from __future__ import annotations

import sys
from decimal import Decimal

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

# ── 川西项目真实 18 家供应商 ──
SUPPLIERS: list[dict] = [
    {"code": "dyjg", "name": "德阳建工", "sort_order": 1},
    {"code": "zjsz", "name": "中机建设", "sort_order": 2},
    {"code": "zclcd", "name": "中储粮成都储藏研究院", "sort_order": 3},
    {"code": "zkjczx", "name": "中凯俊成咨询", "sort_order": 4},
    {"code": "sccd", "name": "四川川东", "sort_order": 5},
    {"code": "scjt", "name": "四川交通", "sort_order": 6},
    {"code": "scjc", "name": "四川建材", "sort_order": 7},
    {"code": "scsj", "name": "四川设计", "sort_order": 8},
    {"code": "cdjg", "name": "成都建工", "sort_order": 9},
    {"code": "ztsj", "name": "中铁设计", "sort_order": 10},
    {"code": "ztjg", "name": "中天建设", "sort_order": 11},
    {"code": "hxjg", "name": "华西建工", "sort_order": 12},
    {"code": "dygj", "name": "德阳国际", "sort_order": 13},
    {"code": "dyjt", "name": "德阳交通", "sort_order": 14},
    {"code": "dyzj", "name": "德阳造价", "sort_order": 15},
    {"code": "dygc", "name": "德阳工程", "sort_order": 16},
    {"code": "dykj", "name": "德阳科技", "sort_order": 17},
    {"code": "dyjc", "name": "德阳检测", "sort_order": 18},
]

# ── 3 套预置节点模板 ──
PRESET_TEMPLATES: list[dict] = [
    {
        "template_name": "监理合同标准节点",
        "biz_type": "supervision",
        "description": "监理合同标准 6 节点（原型：CX009 中凯俊成）",
        "is_preset": True,
        "stages": [
            {"order": 1, "node_name": "合同签订", "agreed_ratio": Decimal("0.10"), "trigger_condition": "签订合同后 7 日内支付", "offset_days": 7},
            {"order": 2, "node_name": "产值达到 50%", "agreed_ratio": Decimal("0.20"), "trigger_condition": "产值达到合同金额 50% 时", "offset_days": 0},
            {"order": 3, "node_name": "竣工验收", "agreed_ratio": Decimal("0.40"), "trigger_condition": "竣工验收合格后", "offset_days": 0},
            {"order": 4, "node_name": "竣工结算", "agreed_ratio": Decimal("0.25"), "trigger_condition": "竣工结算审核完成后", "offset_days": 0},
            {"order": 5, "node_name": "决算批复", "agreed_ratio": Decimal("0.05"), "trigger_condition": "决算批复后付清", "offset_days": 0},
            {"order": 0, "node_name": "汇总", "agreed_ratio": Decimal("1.00"), "trigger_condition": "累计已付/剩余未付", "offset_days": 0},
        ],
    },
    {
        "template_name": "设计合同标准节点",
        "biz_type": "design",
        "description": "设计合同标准 5 节点（原型：CX005 中储粮研究院）",
        "is_preset": True,
        "stages": [
            {"order": 1, "node_name": "合同签订", "agreed_ratio": Decimal("0.30"), "trigger_condition": "签订合同后 7 日内支付", "offset_days": 7},
            {"order": 2, "node_name": "施工图交付", "agreed_ratio": Decimal("0.40"), "trigger_condition": "全套施工图交付后", "offset_days": 0},
            {"order": 3, "node_name": "竣工验收", "agreed_ratio": Decimal("0.20"), "trigger_condition": "竣工验收合格后", "offset_days": 0},
            {"order": 4, "node_name": "竣工结算", "agreed_ratio": Decimal("0.10"), "trigger_condition": "竣工结算审核完成后", "offset_days": 0},
            {"order": 0, "node_name": "汇总", "agreed_ratio": Decimal("1.00"), "trigger_condition": "累计已付/剩余未付", "offset_days": 0},
        ],
    },
    {
        "template_name": "检测合同标准节点",
        "biz_type": "testing",
        "description": "检测合同标准 3 节点（原型：CX016 检测合同）",
        "is_preset": True,
        "stages": [
            {"order": 1, "node_name": "合同签订", "agreed_ratio": Decimal("0.30"), "trigger_condition": "签订合同后 7 日内支付", "offset_days": 7},
            {"order": 2, "node_name": "检测报告交付", "agreed_ratio": Decimal("0.60"), "trigger_condition": "检测报告交付后", "offset_days": 0},
            {"order": 0, "node_name": "汇总", "agreed_ratio": Decimal("1.00"), "trigger_condition": "累计已付/剩余未付", "offset_days": 0},
        ],
    },
]


def seed_dict_suppliers(session: Session) -> int:
    """预填 18 家供应商字典。返回新增行数。"""
    from app.models.dict_tables import DictSupplier

    count = 0
    for item in SUPPLIERS:
        existing = session.execute(
            select(DictSupplier).where(DictSupplier.code == item["code"])
        ).scalar_one_or_none()
        if existing:
            continue
        supplier = DictSupplier(
            code=item["code"],
            name=item["name"],
            sort_order=item["sort_order"],
            is_active=True,
        )
        session.add(supplier)
        count += 1

    session.flush()
    return count


def seed_node_templates(session: Session) -> int:
    """预填 3 套节点模板。返回新增行数。"""
    from app.models.node_template import NodeTemplate
    from datetime import datetime, UTC

    count = 0
    for item in PRESET_TEMPLATES:
        existing = session.execute(
            select(NodeTemplate).where(NodeTemplate.template_name == item["template_name"])
        ).scalar_one_or_none()
        if existing:
            continue
        template = NodeTemplate(
            template_name=item["template_name"],
            biz_type=item["biz_type"],
            description=item["description"],
            is_preset=True,
            stages=[
                {
                    "order": s["order"],
                    "node_name": s["node_name"],
                    "agreed_ratio": float(s["agreed_ratio"]),
                    "trigger_condition": s["trigger_condition"],
                    "offset_days": s["offset_days"],
                }
                for s in item["stages"]
            ],
        )
        session.add(template)
        count += 1

    session.flush()
    return count


# ── 合同费用分项种子数据（按 contract_no 匹配） ──
CONTRACT_FEE_ITEMS: list[dict] = [
    # 施工合同 — 德阳建工 (CX001)
    {"contract_no": "CX001", "items": [
        {"item_name": "建筑安装工程费", "current_ratio": 0.10, "sort_order": 1},
        {"item_name": "安全文明施工费", "current_ratio": 0.50, "sort_order": 2},
    ]},
    # 设备合同 — 中机建设 (CX005)
    {"contract_no": "CX005", "items": [
        {"item_name": "设备安装调试费", "contract_amount": 32564430, "current_ratio": 0.20, "sort_order": 1},
    ]},
    # 设计合同 — 中储粮成都储藏研究院 (CX003)
    {"contract_no": "CX003", "items": [
        {"item_name": "设计费", "contract_amount": 1937160, "current_ratio": 0.20, "sort_order": 1},
    ]},
    # 监理合同 — 中凯俊成咨询 (CX011)
    {"contract_no": "CX011", "items": [
        {"item_name": "工程监理服务费", "current_ratio": 0.10, "sort_order": 1},
        {"item_name": "造价咨询服务费", "current_ratio": 0.20, "sort_order": 2},
        {"item_name": "竣工结算服务费", "current_ratio": 0.30, "sort_order": 3},
    ]},
]


def seed_contract_fee_items(session: Session) -> int:
    """为已有合同预填费用分项模板。返回新增行数。"""
    from app.models.contract import Contract
    from app.models.contract_fee_item import ContractFeeItem

    count = 0
    for entry in CONTRACT_FEE_ITEMS:
        contract = session.execute(
            select(Contract).where(Contract.contract_no == entry["contract_no"])
        ).scalar_one_or_none()
        if not contract:
            continue

        for item in entry["items"]:
            existing = session.execute(
                select(ContractFeeItem).where(
                    ContractFeeItem.contract_id == contract.id,
                    ContractFeeItem.item_name == item["item_name"],
                )
            ).scalar_one_or_none()
            if existing:
                continue
            fee_item = ContractFeeItem(
                contract_id=contract.id,
                item_name=item["item_name"],
                contract_amount=item.get("contract_amount"),
                current_ratio=item.get("current_ratio"),
                sort_order=item.get("sort_order", 0),
            )
            session.add(fee_item)
            count += 1

    session.flush()
    return count


def seed_backfill_review_mode(session: Session) -> int:
    """将存量 NULL review_mode 回填为 'daily_aggregate'。返回更新的行数。"""
    from app.models.contract import Contract

    result = session.execute(
        text("UPDATE t_contracts SET review_mode = 'daily_aggregate' WHERE review_mode IS NULL")
    )
    session.flush()
    return result.rowcount


def seed_all(dry_run: bool = False) -> dict:
    """运行所有种子数据。

    Args:
        dry_run: True 则只打印，不写入数据库。

    Returns:
        种子结果统计。
    """
    from app.core.config import settings

    # 构建同步连接 URL
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(sync_url)

    with Session(engine) as session:
        sup_count = seed_dict_suppliers(session)
        tmp_count = seed_node_templates(session)
        bf_count = seed_backfill_review_mode(session)
        fee_count = seed_contract_fee_items(session)

        if dry_run:
            session.rollback()
            print("[DRY RUN] 未写入数据库")
        else:
            session.commit()
            print("[COMMIT] 已写入数据库")

        return {
            "suppliers_added": sup_count,
            "templates_added": tmp_count,
            "backfilled_review_mode": bf_count,
            "fee_items_added": fee_count,
        }


def main():
    """入口：从命令行调用。"""
    dry_run = "--dry-run" in sys.argv
    result = seed_all(dry_run=dry_run)
    print(f"供应商新增: {result['suppliers_added']}")
    print(f"节点模板新增: {result['templates_added']}")
    print(f"回填 review_mode: {result['backfilled_review_mode']} 行")
    print(f"费用分项模板新增: {result['fee_items_added']} 行")
    print("种子数据完成!")


if __name__ == "__main__":
    main()
