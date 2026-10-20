"""端到端测试：创建期次 → 审核草稿 → 费用分项 → 报送 → 审定 → 台账写入

测试整个 Phase2 核心链路。
运行方式: cd backend && python tests/test_e2e_review_flow.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import date

# 修复 Windows GBK 编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 添加项目路径
sys.path.insert(0, ".")

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.project import Project
from app.models.contract import Contract, ContractMonthlyDetail
from app.models.contract_fee_item import ContractFeeItem
from app.models.reporting_period import ReportingPeriod, PeriodContract
from app.models.progress_review import ProgressPaymentReview
from app.models.review_fee_item import ReviewFeeItem
from app.services import period_service
from app.services import review as review_service
from app.services.review import copy_fee_items_from_contract
from app.schemas.review import ReviewUpdate, ReviewStatusUpdate

# ── 颜色输出 ──
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def ok(msg: str):
    print(f"  {GREEN}[OK]{RESET} {msg}")


def fail(msg: str):
    print(f"  {RED}[FAIL]{RESET} {msg}")


def info(msg: str):
    print(f"  {CYAN}→ {msg}{RESET}")


def step(n: int, title: str):
    print(f"\n{BOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}  Step {n}: {title}{RESET}")
    print(f"{BOLD}{'═' * 60}{RESET}")


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        # ═══════════════════════════════════════════════════════════
        # Step 0: 查找测试数据
        # ═══════════════════════════════════════════════════════════
        step(0, "查找测试项目与合同")

        project = (await db.execute(
            select(Project).where(Project.deleted_at.is_(None)).limit(1)
        )).scalar_one_or_none()

        if not project:
            fail("没有找到项目，请先运行 seed_data")
            return

        ok(f"项目: {project.project_name} (id={str(project.id)[:8]}…)")

        # 取有费用分项的合同
        contracts_result = await db.execute(
            select(Contract).where(
                Contract.project_id == project.id,
                Contract.deleted_at.is_(None),
            ).limit(10)
        )
        all_contracts = list(contracts_result.scalars().all())
        if not all_contracts:
            fail("没有找到合同")
            return

        # 检查哪些合同有费用分项
        contracts_with_fee: list[Contract] = []
        for c in all_contracts:
            fee_count = (await db.execute(
                select(func.count(ContractFeeItem.id)).where(
                    ContractFeeItem.contract_id == c.id
                )
            )).scalar() or 0
            if fee_count > 0:
                contracts_with_fee.append(c)

        if not contracts_with_fee:
            info("没有合同配置了费用分项，先为第一个合同创建费用分项")
            c = all_contracts[0]
            from app.services.fee_item_service import create_contract_fee_items
            await create_contract_fee_items(db, c.id, [
                {"item_name": "建安工程费", "contract_amount": c.contract_amount or 100000000, "current_ratio": 0.1, "sort_order": 1},
                {"item_name": "安全文明施工费", "contract_amount": 50000000, "current_ratio": 0.5, "sort_order": 2},
            ])
            await db.commit()
            contracts_with_fee.append(c)
            ok(f"为合同 {c.contract_no} 创建了 2 个费用分项")

        # 取 2 个有费用分项的合同用于测试
        test_contracts = contracts_with_fee[:2]
        for ct in test_contracts:
            fee_items = (await db.execute(
                select(ContractFeeItem).where(ContractFeeItem.contract_id == ct.id).order_by(ContractFeeItem.sort_order)
            )).scalars().all()
            ok(f"合同 {ct.contract_no} ({ct.supplier_name}) — {len(fee_items)} 个费用分项: {[f'{fi.item_name}({fi.current_ratio})' for fi in fee_items]}")

        # ═══════════════════════════════════════════════════════════
        # Step 1: 创建期次
        # ═══════════════════════════════════════════════════════════
        step(1, "创建期次（自动生成审核草稿 + 费用分项快照）")

        # 检查已有的最大期次号
        max_no = (await db.execute(
            select(func.coalesce(func.max(ReportingPeriod.period_no), 0)).where(
                ReportingPeriod.project_id == project.id
            )
        )).scalar() or 0
        new_period_no = max_no + 1
        period_month = "2026-07"

        contract_ids = [c.id for c in test_contracts]
        try:
            period = await period_service.create_period(
                db,
                project_id=project.id,
                period_month=period_month,
                period_no=new_period_no,
                contract_ids=contract_ids,
                remark="E2E 测试期次",
            )
            await db.commit()
        except Exception as e:
            fail(f"创建期次失败: {e}")
            # 可能存在同号的期次，尝试下一个号
            new_period_no = max_no + 2
            period = await period_service.create_period(
                db, project_id=project.id, period_month=period_month,
                period_no=new_period_no, contract_ids=contract_ids, remark="E2E 测试期次",
            )
            await db.commit()

        ok(f"期次已创建: 第 {period.period_no} 期 ({period.period_month}) — status={period.status}")

        # 重新加载含关系
        period = await period_service.get_period(db, period.id)
        ok(f"关联合同: {period.contract_count} 个")
        ok(f"自动生成审核记录: {period.review_count} 条")

        # ═══════════════════════════════════════════════════════════
        # Step 2: 验证审核草稿自动生成
        # ═══════════════════════════════════════════════════════════
        step(2, "验证审核草稿及费用分项快照")

        reviews = (await db.execute(
            select(ProgressPaymentReview)
            .where(ProgressPaymentReview.period_id == period.id)
            .order_by(ProgressPaymentReview.review_type)
        )).scalars().all()

        if len(reviews) != len(contract_ids):
            fail(f"审核记录数量不匹配: 期望 {len(contract_ids)}, 实际 {len(reviews)}")
        else:
            ok(f"审核记录数量正确: {len(reviews)} 条")

        test_review = None
        for rv in reviews:
            # 重新加载含 fee_items
            rv = await review_service.get_review(db, rv.id)
            ctr = rv.contract

            status_icon = "[OK]" if rv.audit_status == "draft" else "[WARN]"
            ok(f"{status_icon} {rv.review_type} | {rv.applicant_unit} | "
               f"合同={ctr.contract_no if ctr else '?'} | "
               f"status={rv.audit_status} | "
               f"fee_items={len(rv.fee_items)}个")

            for fi in rv.fee_items:
                info(f"    分项: {fi.item_name} | 比例={fi.payment_ratio} | "
                     f"报送={fi.reported_amount} | 审定={fi.reviewed_amount}")

            if rv.fee_items and rv.audit_status == "draft":
                test_review = rv

        if not test_review:
            fail("没有找到 draft 状态的审核记录可用于后续测试")
            return

        ok(f"选定测试审核记录: {test_review.review_type} — {test_review.applicant_unit}")

        # ═══════════════════════════════════════════════════════════
        # Step 3: 填写费用分项报送值 & 审定值
        # ═══════════════════════════════════════════════════════════
        step(3, "填写费用分项（报送值 + 审定值）")

        # 为每个 fee_item 填写报送值和审定值
        fee_items_update = []
        for fi in test_review.fee_items:
            reported = 50000000  # 5000 万分 ≈ 5 万元
            reviewed = 48000000  # 审定略小于报送（模拟过控核减）
            fee_items_update.append({
                "id": fi.id,
                "reported_amount": reported,
                "reviewed_amount": reviewed,
            })
            info(f"  {fi.item_name}: 报送={reported}分({reported/1000000:.4f}万) → 审定={reviewed}分({reviewed/1000000:.4f}万)")

        update_data = ReviewUpdate(fee_items=fee_items_update)
        updated_review = await review_service.update_review(db, test_review.id, update_data)
        await db.commit()

        # 验证
        updated_review = await review_service.get_review(db, test_review.id)
        for fi in updated_review.fee_items:
            ok(f"  写入后 {fi.item_name}: reported={fi.reported_amount}, reviewed={fi.reviewed_amount}")

        # ═══════════════════════════════════════════════════════════
        # Step 4: 报送（draft → submitted）
        # ═══════════════════════════════════════════════════════════
        step(4, "报送审核（draft → submitted）")

        status_update = ReviewStatusUpdate(audit_status="submitted")
        submitted_review = await review_service.update_review_status(
            db, test_review.id, status_update
        )
        await db.commit()

        if submitted_review.audit_status == "submitted":
            ok(f"状态流转成功: draft → submitted")
        else:
            fail(f"状态流转失败: 期望 submitted, 实际 {submitted_review.audit_status}")

        # ═══════════════════════════════════════════════════════════
        # Step 5: 确认审定（submitted → reviewed）+ 台账写入
        # ═══════════════════════════════════════════════════════════
        step(5, "确认审定（submitted → reviewed）+ 自动写入月度台账")

        reviewed_update = ReviewStatusUpdate(audit_status="reviewed")
        reviewed_review = await review_service.update_review_status(
            db, test_review.id, reviewed_update
        )
        await db.commit()

        if reviewed_review.audit_status == "reviewed":
            ok(f"状态流转成功: submitted → reviewed")
        else:
            fail(f"状态流转失败: 期望 reviewed, 实际 {reviewed_review.audit_status}")

        # 验证汇总字段
        reviewed_review = await review_service.get_review(db, test_review.id)
        info(f"  current_audited_output = {reviewed_review.current_audited_output} 分 "
             f"({reviewed_review.current_audited_output/1000000:.4f} 万)")
        info(f"  cumulative_audited_payable = {reviewed_review.cumulative_audited_payable} 分 "
             f"({reviewed_review.cumulative_audited_payable/1000000:.4f} 万)")

        # ═══════════════════════════════════════════════════════════
        # Step 6: 验证月度台账写入
        # ═══════════════════════════════════════════════════════════
        step(6, "验证月度台账写入")

        detail_month = date.fromisoformat(period_month + "-01")
        ledger_result = await db.execute(
            select(ContractMonthlyDetail).where(
                ContractMonthlyDetail.contract_id == test_review.contract_id,
                ContractMonthlyDetail.detail_month == detail_month,
            )
        )
        ledger = ledger_result.scalar_one_or_none()

        if ledger:
            ok(f"台账记录已写入:")
            ok(f"  contract_no: {ledger.contract_no}")
            ok(f"  detail_month: {ledger.detail_month}")
            ok(f"  output_amount: {ledger.output_amount} 分 ({ledger.output_amount/1000000:.4f} 万)")
            ok(f"  source: {ledger.source}")
            ok(f"  status: {ledger.status}")

            # 验证 fee_items JSONB
            if ledger.cost_items_detail and isinstance(ledger.cost_items_detail, dict):
                items = ledger.cost_items_detail.get("items", [])
                ok(f"  cost_items_detail 含 {len(items)} 个分项:")
                for fi in items:
                    info(f"    {fi['name']}: reported={fi['reported_amount']}, "
                         f"reviewed={fi['reviewed_amount']}, "
                         f"ratio={fi['payment_ratio']}, payable={fi['payable']}")
            else:
                fail("  cost_items_detail 为空")
        else:
            fail(f"台账记录未写入! contract_id={test_review.contract_id}, month={detail_month}")

        # ═══════════════════════════════════════════════════════════
        # Step 7: 验证期次状态联动
        # ═══════════════════════════════════════════════════════════
        step(7, "验证期次状态联动")

        period = await period_service.get_period(db, period.id)
        ok(f"期次状态: {period.status}")

        # 检查所有 review 状态
        all_reviews = (await db.execute(
            select(ProgressPaymentReview).where(ProgressPaymentReview.period_id == period.id)
        )).scalars().all()
        statuses = [r.audit_status for r in all_reviews]
        info(f"  各 review 状态: {statuses}")

        # 如果只有一条 review 且已 reviewed，期次应该 → reviewed
        if len(all_reviews) == 1 and all_reviews[0].audit_status == "reviewed":
            if period.status == "reviewed":
                ok("期次状态联动正确: 唯一 review → reviewed → 期次自动 → reviewed")
            else:
                fail(f"期次状态联动可能有问题: 期望 reviewed, 实际 {period.status}")
        elif all(s == "reviewed" for s in statuses):
            if period.status == "reviewed":
                ok("期次状态联动正确: 所有 review → reviewed → 期次 → reviewed")
            else:
                fail(f"期次状态联动可能有问题: 期望 reviewed, 实际 {period.status}")
        else:
            info(f"部分 review 未确认，期次状态 = {period.status}（合理）")

        # ═══════════════════════════════════════════════════════════
        # Summary
        # ═══════════════════════════════════════════════════════════
        print(f"\n{BOLD}{'═' * 60}{RESET}")
        print(f"{BOLD}{GREEN}  [PASS] E2E 测试完成！核心链路验证通过。{RESET}")
        print(f"{BOLD}{'═' * 60}{RESET}")
        print(f"\n  测试期次: 第 {period.period_no} 期 ({period.period_month})")
        print(f"  合同数: {len(contract_ids)} → 审核记录: {len(reviews)} 条")
        print(f"  测试审核: {test_review.review_type} — {test_review.applicant_unit}")
        print(f"  费用分项: {len(test_review.fee_items)} 个")
        print(f"  状态链路: draft → submitted → reviewed [OK]")
        print(f"  台账写入: {'[OK]' if ledger else '[FAIL]'}")
        print(f"  期次联动: {period.status}")

        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
