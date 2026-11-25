"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

DECISION_ALLOW = "allow"
DECISION_DENY = "deny"
ALLOWED_DECISIONS = frozenset({DECISION_ALLOW, DECISION_DENY})

DANGEROUS_TOOL_NAMES = frozenset(
    {"shell_exec", "http_fetch_any", "read_secrets", "rm_rf"}
)

REQUIRED_REPORT_SECTIONS = (
    "允许列表",
    "校验规则",
    "拒绝样例",
    "与注入的关系",
    "明日预告",
)

ORDER_DB: dict[str, dict[str, str]] = {
    "ORD-1001": {
        "status": "shipped",
        "total": "128.00",
        "currency": "CNY",
        "city": "上海",
        "item": "机械键盘",
    },
    "ORD-1002": {
        "status": "processing",
        "total": "59.90",
        "currency": "CNY",
        "city": "杭州",
        "item": "USB-C 数据线",
    },
}


@dataclass(frozen=True)
class ToolSpec:
    """允许列表中的一条工具规格。"""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]
    enabled: bool = True


@dataclass(frozen=True)
class ValidationResult:
    """参数校验结果。"""

    ok: bool
    errors: tuple[str, ...]


@dataclass(frozen=True)
class GuardDecision:
    """对一次工具调用的授权决策。"""

    decision: str
    tool_name: str
    reason: str
    normalized_args: dict[str, Any] | None = None


def normalize_tool_name(name: str) -> str:
    """去掉首尾空白并转小写；空字符串抛 ValueError。"""
    normalized = name.strip().lower()
    if not normalized:
        raise ValueError("tool name must not be empty")
    return normalized


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白压成单个空格。"""
    return " ".join(text.split())


def order_lookup(order_id: str) -> str:
    """按订单号返回一行摘要。"""
    cleaned = normalize_text(order_id)
    if not cleaned:
        raise ValueError("order_id must not be empty")
    if cleaned not in ORDER_DB:
        raise KeyError(f"order_id not found: {cleaned}")
    row = ORDER_DB[cleaned]
    return (
        f"订单 {cleaned}：status={row['status']}，合计 {row['total']} {row['currency']}，"
        f"收货地 {row['city']}，商品 {row['item']}"
    )


def get_time(unit: str = "s") -> str:
    """返回教学用固定时间戳字符串。"""
    normalized = unit.strip().lower()
    if normalized == "s":
        return "1700000000"
    if normalized == "ms":
        return "1700000000000"
    raise ValueError("unit must be s or ms")


def build_default_allowlist() -> dict[str, ToolSpec]:
    """构建默认允许列表。"""
    order_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "minLength": 1},
        },
        "required": ["order_id"],
        "additionalProperties": False,
    }
    time_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "unit": {"type": "string", "enum": ["s", "ms"]},
        },
        "required": [],
        "additionalProperties": False,
    }
    specs = (
        ToolSpec(
            name="order_lookup",
            description="按订单号查询只读状态摘要",
            parameters=order_schema,
            handler=order_lookup,
            enabled=True,
        ),
        ToolSpec(
            name="get_time",
            description="返回教学用固定时间戳（s 或 ms）",
            parameters=time_schema,
            handler=get_time,
            enabled=True,
        ),
    )
    allowlist = {spec.name: spec for spec in specs}
    for dangerous in DANGEROUS_TOOL_NAMES:
        assert dangerous not in allowlist
    return allowlist


def validate_args(
    args: Any,
    schema: dict[str, Any],
) -> ValidationResult:
    """按迷你 JSON Schema 校验 args。"""
    if not isinstance(args, dict):
        return ValidationResult(ok=False, errors=("args type must be object/dict",))

    errors: list[str] = []
    required = schema.get("required") or []
    properties: dict[str, Any] = schema.get("properties") or {}
    additional = schema.get("additionalProperties", False)

    for key in required:
        if key not in args:
            errors.append(f"missing required field: {key}")

    if additional is False:
        for key in args:
            if key not in properties:
                errors.append(f"additional property not allowed: {key}")

    for key, value in args.items():
        if key not in properties:
            continue
        prop = properties[key]
        expected_type = prop.get("type")
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"field {key} type must be string")
            continue
        if "minLength" in prop and isinstance(value, str):
            min_length = prop["minLength"]
            if len(value) < min_length:
                errors.append(f"field {key} minLength is {min_length}")
        if "enum" in prop and value not in prop["enum"]:
            errors.append(f"field {key} enum mismatch")

    return ValidationResult(ok=not errors, errors=tuple(errors))


def authorize_tool_call(
    tool_name: str,
    args: Any,
    allowlist: dict[str, ToolSpec] | None = None,
) -> GuardDecision:
    """对工具调用做授权。"""
    try:
        normalized_name = normalize_tool_name(tool_name)
    except ValueError:
        return GuardDecision(
            decision=DECISION_DENY,
            tool_name=tool_name,
            reason="invalid tool name",
            normalized_args=None,
        )

    resolved = allowlist if allowlist is not None else build_default_allowlist()
    spec = resolved.get(normalized_name)
    if spec is None:
        return GuardDecision(
            decision=DECISION_DENY,
            tool_name=normalized_name,
            reason="unknown tool not in allowlist",
            normalized_args=None,
        )
    if not spec.enabled:
        return GuardDecision(
            decision=DECISION_DENY,
            tool_name=normalized_name,
            reason="tool is disabled",
            normalized_args=None,
        )

    validation = validate_args(args, spec.parameters)
    if not validation.ok:
        return GuardDecision(
            decision=DECISION_DENY,
            tool_name=normalized_name,
            reason="; ".join(validation.errors),
            normalized_args=None,
        )

    assert isinstance(args, dict)
    return GuardDecision(
        decision=DECISION_ALLOW,
        tool_name=normalized_name,
        reason="allow: tool on allowlist and args valid",
        normalized_args=dict(args),
    )


def guarded_invoke(
    tool_name: str,
    args: dict[str, Any] | None = None,
    allowlist: dict[str, ToolSpec] | None = None,
) -> Any:
    """先 authorize，再调用 handler。"""
    payload = {} if args is None else args
    decision = authorize_tool_call(tool_name, payload, allowlist)
    if decision.decision == DECISION_DENY:
        raise PermissionError(decision.reason)
    resolved = allowlist if allowlist is not None else build_default_allowlist()
    spec = resolved[decision.tool_name]
    assert decision.normalized_args is not None
    return spec.handler(**decision.normalized_args)


def render_guard_report(
    allowlist: dict[str, ToolSpec] | None = None,
    title: str = "Week 12 · 工具白名单与参数校验",
) -> str:
    """渲染 Markdown 防护报告。"""
    resolved = allowlist if allowlist is not None else build_default_allowlist()

    allow_lines = [
        "| 工具 | enabled | required | 说明 |",
        "|------|---------|----------|------|",
    ]
    for name in sorted(resolved.keys()):
        spec = resolved[name]
        required = ", ".join(spec.parameters.get("required") or []) or "（无）"
        allow_lines.append(
            f"| `{name}` | {spec.enabled} | {required} | "
            f"{normalize_text(spec.description)} |"
        )

    rule_lines = [
        "- 默认拒绝：未出现在允许列表的工具名一律 deny",
        "- 名称规范化：strip + lower，避免大小写绕过",
        "- Schema：检查 required / type / minLength / enum / additionalProperties",
        "- 校验在 handler 之前；失败原因写入 GuardDecision.reason",
    ]

    deny_lines = [
        "- `shell_exec` + 任意参数 → unknown tool not in allowlist",
        "- `order_lookup` + `{}` → missing required field: order_id",
        "- `order_lookup` + `{\"order_id\": 123}` → field order_id type must be string",
        "- disabled 的工具 → tool is disabled",
    ]

    inject_lines = [
        "- Day 56：注入会让模型「想」调用危险工具或乱参数",
        "- Day 57：就算模型输出了危险名，Guard 也不会执行",
        "- 提示词禁令是软约束；白名单 + Schema 才是硬门禁",
    ]

    parts = [
        f"# {normalize_text(title)}",
        "",
        "## 允许列表",
        "",
        "\n".join(allow_lines),
        "",
        "## 校验规则",
        "",
        "\n".join(rule_lines),
        "",
        "## 拒绝样例",
        "",
        "\n".join(deny_lines),
        "",
        "## 与注入的关系",
        "",
        "\n".join(inject_lines),
        "",
        "## 明日预告",
        "",
        "- Day 58：Mock LLM 单测——用假模型覆盖合法调用 / Guard 拒绝 / max_steps 等分支",
        "- 随后：HITL 确认钩子，以及 `tool-agent` 里程碑验收",
        "",
    ]
    return "\n".join(parts)
