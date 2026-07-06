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
            stages={"stages": [
                {
                    "order": s["order"],
                    "node_name": s["node_name"],
                    "agreed_ratio": float(s["agreed_ratio"]),
                    "trigger_condition": s["trigger_condition"],
                    "offset_days": s["offset_days"],
                }
                for s in item["stages"]
            ]},
        )
        session.add(template)
        count += 1

    session.flush()
    return count


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

        if dry_run:
            session.rollback()
            print("[DRY RUN] 未写入数据库")
        else:
            session.commit()
            print("[COMMIT] 已写入数据库")

        return {
            "suppliers_added": sup_count,
            "templates_added": tmp_count,
        }


def main():
    """入口：从命令行调用。"""
    dry_run = "--dry-run" in sys.argv
    result = seed_all(dry_run=dry_run)
    print(f"供应商新增: {result['suppliers_added']}")
    print(f"节点模板新增: {result['templates_added']}")
    print("种子数据完成!")


if __name__ == "__main__":
    main()
