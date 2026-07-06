"""数据校验器 —— 5 类校验规则

1. 必填校验 (required): 字段值非空
2. 类型校验 (type):    字段类型正确 (uuid / date / int / str)
3. 范围校验 (range):   数值在允许范围内
4. 引用校验 (reference): 外键引用存在
5. 唯一性校验 (unique): 组合字段唯一（warning，不阻断）
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class ValidationResult:
    """单条校验结果。"""

    field: str
    code: str
    message: str
    severity: str  # "error" | "warning" | "info"
    rule_type: str  # "required" | "type" | "range" | "reference" | "unique"


def validate_required(row: dict[str, Any], required_fields: list[str]) -> list[ValidationResult]:
    """必填校验：检查指定字段是否存在且非空。"""
    errors: list[ValidationResult] = []
    for field in required_fields:
        value = row.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            errors.append(ValidationResult(
                field=field,
                code="REQUIRED",
                message=f"'{field}' 为必填字段",
                severity="error",
                rule_type="required",
            ))
    return errors


def validate_types(row: dict[str, Any], type_map: dict[str, str]) -> list[ValidationResult]:
    """类型校验：检查字段值是否符合指定类型。

    type_map 示例: {"project_id": "uuid", "data_date": "date", "amount": "int"}
    """
    errors: list[ValidationResult] = []
    for field, expected_type in type_map.items():
        value = row.get(field)
        if value is None:
            continue  # 必填由 validate_required 处理

        if expected_type == "uuid":
            if not isinstance(value, uuid.UUID):
                try:
                    uuid.UUID(str(value))
                except (ValueError, AttributeError):
                    errors.append(ValidationResult(
                        field=field,
                        code="TYPE_MISMATCH",
                        message=f"'{field}' 期望 UUID 类型，实际值: {repr(value)}",
                        severity="error",
                        rule_type="type",
                    ))

        elif expected_type == "date":
            if not isinstance(value, date):
                errors.append(ValidationResult(
                    field=field,
                    code="TYPE_MISMATCH",
                    message=f"'{field}' 期望日期类型，实际值: {repr(value)}",
                    severity="error",
                    rule_type="type",
                ))

        elif expected_type in ("int", "bigint_positive", "bigint_non_negative"):
            if not isinstance(value, (int, float)):
                errors.append(ValidationResult(
                    field=field,
                    code="TYPE_MISMATCH",
                    message=f"'{field}' 期望数值类型，实际值: {repr(value)}",
                    severity="error",
                    rule_type="type",
                ))

        elif expected_type == "str":
            if not isinstance(value, str):
                errors.append(ValidationResult(
                    field=field,
                    code="TYPE_MISMATCH",
                    message=f"'{field}' 期望字符串类型",
                    severity="error",
                    rule_type="type",
                ))

    return errors


def validate_ranges(row: dict[str, Any], range_map: dict[str, tuple[int | float, int | float]]) -> list[ValidationResult]:
    """范围校验：检查数值字段是否在 [min, max] 区间内。

    range_map 示例: {"amount": [1, 10_000_000_000_00]}
    """
    errors: list[ValidationResult] = []
    for field, (min_val, max_val) in range_map.items():
        value = row.get(field)
        if value is None:
            continue
        try:
            num = float(value)
            if num < min_val or num > max_val:
                errors.append(ValidationResult(
                    field=field,
                    code="AMOUNT_OUT_OF_RANGE",
                    message=f"'{field}' 值 {num} 超出范围 [{min_val}, {max_val}]",
                    severity="error",
                    rule_type="range",
                ))
        except (TypeError, ValueError):
            pass  # 类型错误由 validate_types 处理

    return errors


async def validate_references(
    row: dict[str, Any],
    ref_map: dict[str, tuple[str, str]],
    db_session: Any,
) -> list[ValidationResult]:
    """引用校验（异步）：检查外键引用是否存在。

    ref_map 示例: {"project_id": ("t_project", "id")}
    注意：当前实现为骨架，实际引用校验在清洗流水线 async 任务中执行。
    """
    # 骨架实现：仅记录引用校验的字段配置
    errors: list[ValidationResult] = []
    for field, (table, column) in ref_map.items():
        value = row.get(field)
        if value is None:
            continue
        # TODO: 执行实际 SQL 检查
        # result = await db_session.execute(
        #     select(func.count()).select_from(table(table)).where(column(column) == value)
        # )
        # if result.scalar() == 0:
        #     errors.append(...)
    return errors


def validate_uniqueness(
    row: dict[str, Any],
    unique_groups: list[list[str]],
    existing_data: list[dict[str, Any]],
) -> list[ValidationResult]:
    """唯一性校验（同步、warning 级别）：检查组合字段是否与已有数据重复。

    不阻断，仅产生 warning。
    """
    errors: list[ValidationResult] = []
    for group in unique_groups:
        # 构建当前行的组合键
        current_key = tuple(row.get(f) for f in group)
        if any(v is None for v in current_key):
            continue  # 有 None 值时不检测唯一性

        for existing_row in existing_data:
            existing_key = tuple(existing_row.get(f) for f in group)
            if current_key == existing_key:
                fields_str = ", ".join(group)
                errors.append(ValidationResult(
                    field=fields_str,
                    code="DUPLICATE_KEY",
                    message=f"组合字段 ({fields_str}) 的值已存在，将产生重复数据",
                    severity="warning",
                    rule_type="unique",
                ))
                break

    return errors


# ═══════════════════════════════════════════════════
# 综合校验入口
# ═══════════════════════════════════════════════════

# 默认校验规则配置
# 注：project_id 不在行级别必填 — 由批次级别继承注入；category 可选。
DEFAULT_VALIDATION_RULES: dict[str, Any] = {
    "required": ["data_date", "item_name", "amount"],
    "types": {
        "data_date": "date",
        "amount": "bigint_positive",
        "planned_quantity": "bigint_non_negative",
        "actual_quantity": "bigint_non_negative",
        "unit_price": "bigint_non_negative",
    },
    "ranges": {
        "amount": [1, 10_000_000_000_00],  # 1 分 ~ 1000 亿元
        "unit_price": [0, 100_000_000_00],  # 0 ~ 1 亿元单价
    },
    "uniqueness": [
        ["data_date", "item_name"],
    ],
    "references": {
        "project_id": ("t_projects", "id"),
    },
}


def validate_row(
    row: dict[str, Any],
    rules: dict[str, Any] | None = None,
    existing_rows: list[dict[str, Any]] | None = None,
) -> list[ValidationResult]:
    """对单行数据执行全部 5 类校验，返回校验结果列表。"""
    r = rules or DEFAULT_VALIDATION_RULES
    existing = existing_rows or []

    results: list[ValidationResult] = []
    results.extend(validate_required(row, r.get("required", [])))
    results.extend(validate_types(row, r.get("types", {})))
    results.extend(validate_ranges(row, r.get("ranges", {})))
    results.extend(validate_uniqueness(row, r.get("uniqueness", []), existing))
    # validate_references 为异步，在清洗流水线中单独调用
    return results
