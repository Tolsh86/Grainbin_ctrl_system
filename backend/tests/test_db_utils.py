"""测试：数据库公共工具 — 分页、软删除过滤、金额转换"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.utils.db import (
    active_filter,
    calc_pages,
    fen_to_wan_yuan,
    fen_to_yuan,
    paginate,
    wan_yuan_to_fen,
    yuan_to_fen,
)
from tests.conftest import NoSoftDeleteModel, TestModel

# ══════════════════════════════════════════════════════
# 金额转换
# ══════════════════════════════════════════════════════


class TestFenToYuan:
    """分 → 元"""

    def test_turnover(self) -> None:
        assert fen_to_yuan(12345) == 123.45

    def test_zero(self) -> None:
        assert fen_to_yuan(0) == 0.0

    def test_hundred_to_one_yuan(self) -> None:
        assert fen_to_yuan(100) == 1.0

    def test_large(self) -> None:
        assert fen_to_yuan(100000000) == 1_000_000.0

    def test_negative(self) -> None:
        assert fen_to_yuan(-500) == -5.0


class TestFenToWanYuan:
    """分 → 万元"""

    def test_turnover(self) -> None:
        # 123456789 分 = 1234567.89 元 = 123.456789 万元
        assert fen_to_wan_yuan(123456789) == pytest.approx(123.456789)

    def test_one_yi(self) -> None:
        # 1 亿分 = 100 万元
        assert fen_to_wan_yuan(100000000) == 100.0

    def test_zero(self) -> None:
        assert fen_to_wan_yuan(0) == 0.0

    def test_negative(self) -> None:
        assert fen_to_wan_yuan(-100000000) == -100.0


class TestYuanToFen:
    """元 → 分"""

    def test_turnover(self) -> None:
        assert yuan_to_fen(123.45) == 12345

    def test_integer(self) -> None:
        assert yuan_to_fen(100) == 10000

    def test_string_with_comma(self) -> None:
        assert yuan_to_fen("1,234.56") == 123456

    def test_chinese_comma(self) -> None:
        assert yuan_to_fen("1，234.56") == 123456

    def test_zero(self) -> None:
        assert yuan_to_fen(0) == 0

    def test_negative(self) -> None:
        assert yuan_to_fen(-1.5) == -150


class TestWanYuanToFen:
    """万元 → 分"""

    def test_turnover(self) -> None:
        assert wan_yuan_to_fen(123.4567) == 123456700

    def test_one_yi(self) -> None:
        # 10000 万元 = 1 亿 = 100 亿分
        assert wan_yuan_to_fen(10000.0) == 10_000_000_000

    def test_string(self) -> None:
        assert wan_yuan_to_fen("12,345.67") == 12345670000

    def test_zero(self) -> None:
        assert wan_yuan_to_fen(0.0) == 0

    def test_negative(self) -> None:
        assert wan_yuan_to_fen(-1.0) == -1_000_000


class TestRoundTrip:
    """四舍五入一致性校验"""

    def test_yuan_roundtrip(self) -> None:
        assert yuan_to_fen(fen_to_yuan(12345)) == 12345

    def test_wan_yuan_roundtrip(self) -> None:
        # 1 亿分 = 100 万元；往返应一致
        assert wan_yuan_to_fen(fen_to_wan_yuan(100_000_000)) == 100_000_000

    def test_precision_float(self) -> None:
        """浮点精度测试：0.1 元 = 10 分"""
        assert yuan_to_fen(0.1) == 10


# ══════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════


class TestCalcPages:
    def test_normal(self) -> None:
        assert calc_pages(100, 20) == 5

    def test_partial_last_page(self) -> None:
        assert calc_pages(101, 20) == 6

    def test_empty(self) -> None:
        assert calc_pages(0, 20) == 0

    def test_invalid_page_size(self) -> None:
        assert calc_pages(100, 0) == 0

    def test_single(self) -> None:
        assert calc_pages(1, 20) == 1


# ══════════════════════════════════════════════════════
# 软删除过滤
# ══════════════════════════════════════════════════════


class TestActiveFilter:
    def test_adds_filter_for_soft_delete_model(self) -> None:
        stmt = select(TestModel)
        filtered = active_filter(stmt, TestModel)
        compiled = str(filtered.compile(compile_kwargs={"literal_binds": True}))
        assert "deleted_at" in compiled
        assert "IS NULL" in compiled

    def test_skips_model_without_deleted_at(self) -> None:
        stmt = select(NoSoftDeleteModel)
        filtered = active_filter(stmt, NoSoftDeleteModel)
        compiled = str(filtered.compile(compile_kwargs={"literal_binds": True}))
        # NoSoftDeleteModel 没有 deleted_at 字段，过滤应无变化
        assert "deleted_at" not in compiled


# ══════════════════════════════════════════════════════
# 分页查询（异步，需要数据库）
# ══════════════════════════════════════════════════════


class TestPaginate:
    """集成测试 — 真实 SQLite 异步数据库"""

    async def test_basic_pagination(self, db_session) -> None:
        """基础分页：每页 3 条，共 6 条未删除记录，应返回第 1 页 3 条"""
        stmt = select(TestModel).order_by(TestModel.id)
        items, total = await paginate(db_session, stmt, model=TestModel, page=1, page_size=3)
        assert total == 6  # 8 条 - 2 条软删除 = 6 条
        assert len(items) == 3
        assert items[0].name == "normal_1"

    async def test_page_2(self, db_session) -> None:
        """第 2 页应返回剩余 3 条"""
        stmt = select(TestModel).order_by(TestModel.id)
        items, total = await paginate(db_session, stmt, model=TestModel, page=2, page_size=3)
        assert total == 6
        assert len(items) == 3
        assert items[0].name == "inactive_1"

    async def test_empty_page(self, db_session) -> None:
        """超出范围的页码返回空列表"""
        stmt = select(TestModel).order_by(TestModel.id)
        items, total = await paginate(db_session, stmt, model=TestModel, page=100, page_size=3)
        assert total == 6
        assert len(items) == 0

    async def test_with_where_clause(self, db_session) -> None:
        """已有 WHERE 条件的分页"""
        stmt = select(TestModel).where(TestModel.status == "inactive").order_by(TestModel.id)
        items, total = await paginate(db_session, stmt, model=TestModel, page=1, page_size=10)
        assert total == 2  # inactive_1 + inactive_2（deleted_2 被软删除过滤）
        assert len(items) == 2
        assert items[0].name == "inactive_1"

    async def test_no_soft_delete_model(self, db_session) -> None:
        """非软删除模型的分页（不应加 deleted_at 过滤）"""
        stmt = select(NoSoftDeleteModel).order_by(NoSoftDeleteModel.id)
        items, total = await paginate(db_session, stmt, model=NoSoftDeleteModel, page=1, page_size=10)
        assert total == 2
        assert len(items) == 2

    async def test_auto_active_false(self, db_session) -> None:
        """关闭自动软删除过滤，所有记录都应返回"""
        stmt = select(TestModel).order_by(TestModel.id)
        items, total = await paginate(db_session, stmt, model=TestModel, page=1, page_size=100, auto_active=False)
        assert total == 8  # 所有 8 条记录（含软删除的）
        assert len(items) == 8

    async def test_custom_count_stmt(self, db_session) -> None:
        """自定义 COUNT 语句"""
        from sqlalchemy import func

        stmt = select(TestModel).where(TestModel.status == "active").order_by(TestModel.id)
        count_stmt = select(func.count(TestModel.id)).where(
            TestModel.status == "active", TestModel.deleted_at.is_(None)
        )
        items, total = await paginate(
            db_session, stmt, model=TestModel, page=1, page_size=10, count_stmt=count_stmt,
        )
        assert total == 4  # active 状态且未删除
        assert len(items) == 4

    async def test_zero_total(self, db_session) -> None:
        """数据为空时（全部软删除），返回空列表和 0 总数"""
        stmt = select(TestModel).where(TestModel.status == "nonexistent")
        items, total = await paginate(db_session, stmt, model=TestModel, page=1, page_size=10)
        assert total == 0
        assert len(items) == 0
