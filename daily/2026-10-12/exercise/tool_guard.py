"""Day 57 练习：工具白名单与参数校验。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——今天是「执行层硬门禁」，不调用真实 LLM。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

DECISION_ALLOW = "allow"
DECISION_DENY = "deny"
ALLOWED_DECISIONS = frozenset({DECISION_ALLOW, DECISION_DENY})

# 教学用：这些名字永远不进默认允许列表
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

# 模拟订单库（只读）
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
    """去掉首尾空白并转小写；空字符串抛 ValueError（消息含 name）。"""
    # TODO
    raise NotImplementedError


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白压成单个空格。"""
    # TODO
    raise NotImplementedError


def order_lookup(order_id: str) -> str:
    """按订单号返回一行摘要；空 id → ValueError；未找到 → KeyError。"""
    # TODO: normalize_text；查 ORDER_DB
    raise NotImplementedError


def get_time(unit: str = "s") -> str:
    """返回教学用固定时间戳字符串。

    - unit 必须是 "s" 或 "ms"（先 normalize_tool_name 风格：strip+lower 亦可直接 strip）
    - "s" → "1700000000"
    - "ms" → "1700000000000"
    - 其他 → ValueError（消息含 unit）
    """
    # TODO
    raise NotImplementedError


def build_default_allowlist() -> dict[str, ToolSpec]:
    """构建默认允许列表（key = normalize 后的工具名）。

    必须包含且仅包含：
    - order_lookup：required=["order_id"]；order_id type=string minLength=1；
      additionalProperties=false
    - get_time：properties.unit type=string enum=["s","ms"]；required=[]；
      additionalProperties=false；unit 可缺省

    不得包含 DANGEROUS_TOOL_NAMES 中的任一名字。
    """
    # TODO
    raise NotImplementedError


def validate_args(
    args: Any,
    schema: dict[str, Any],
) -> ValidationResult:
    """按迷你 JSON Schema 校验 args。

    规则（按顺序累积 errors，全部检查完再返回）：
    1. args 不是 dict → 一条错误，消息含 type，并立即返回 ok=False
    2. required 列表中缺失的键 → 错误含 missing 与字段名
    3. additionalProperties 为 False（或缺省按 False）时，多余键 → 错误含 additional
    4. 对 schema.properties 中出现且 args 也有的字段：
       - type=="string" 但值不是 str → 错误含 type 与字段名
       - minLength 存在且 len(值) < minLength → 错误含 minLength 与字段名
       - enum 存在且值不在枚举中 → 错误含 enum 与字段名
    5. 无错误 → ok=True, errors=()
    """
    # TODO
    raise NotImplementedError


def authorize_tool_call(
    tool_name: str,
    args: Any,
    allowlist: dict[str, ToolSpec] | None = None,
) -> GuardDecision:
    """对工具调用做授权。

    流程：
    1. normalize_tool_name(tool_name)；若抛错 → deny，reason 含 name
    2. allowlist 默认 build_default_allowlist()
    3. 名称不在 allowlist → deny，reason 含 unknown 或 allowlist
    4. spec.enabled 为 False → deny，reason 含 disabled
    5. validate_args；失败 → deny，reason 用 "; ".join(errors)
    6. 成功 → allow，reason 含 allow，normalized_args 为传入的 args 浅拷贝 dict
    """
    # TODO
    raise NotImplementedError


def guarded_invoke(
    tool_name: str,
    args: dict[str, Any] | None = None,
    allowlist: dict[str, ToolSpec] | None = None,
) -> Any:
    """先 authorize，再调用 handler。

    - deny → 抛 PermissionError，消息包含 reason
    - allow → 以 **normalized_args 调用 handler 并返回结果
    - args 为 None 时按 {} 处理
    """
    # TODO
    raise NotImplementedError


def render_guard_report(
    allowlist: dict[str, ToolSpec] | None = None,
    title: str = "Week 12 · 工具白名单与参数校验",
) -> str:
    """渲染 Markdown 防护报告，必须包含 REQUIRED_REPORT_SECTIONS 全部二级标题。"""
    # TODO
    raise NotImplementedError
