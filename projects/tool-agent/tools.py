"""内置工具：时间 / 计算器 / 只读文件 / 假 HTTP / 业务副作用（供 HITL 演示）。

本文件在练习中已给齐，今日勿改。
只用标准库；不发起真实网络请求。
"""

from __future__ import annotations

import ast
import operator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

# ---------- 安全表达式计算器（仅字面量算术） ----------

_BIN_OPS: dict[type, Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS: dict[type, Callable[[Any], Any]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def safe_calculate(expression: str) -> float:
    """安全求值：只允许数字与 + - * / // % ** 以及括号。"""
    text = expression.strip()
    if not text:
        raise ValueError("expression must not be empty")
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"invalid expression: {exc}") from exc
    return float(_eval_node(tree.body))


def _eval_node(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    raise ValueError("expression contains unsupported syntax")


# ---------- 假 HTTP（白名单 host → 固定正文） ----------

FAKE_HTTP_PAGES: dict[str, str] = {
    "example.com": "Example Domain — 用于文档与测试的占位站。",
    "httpbin.org": "httpbin mock: {\"ok\": true, \"service\": \"httpbin\"}",
    "docs.python.org": "Python 官方文档首页摘要（假响应）。",
}


def fake_http_get(url: str) -> str:
    """仅允许 https，且 host 在白名单；返回假页面正文。"""
    raw = url.strip()
    if not raw:
        raise ValueError("url must not be empty")
    parsed = urlparse(raw)
    if parsed.scheme != "https":
        raise ValueError("only https is allowed")
    host = (parsed.hostname or "").lower()
    if host not in FAKE_HTTP_PAGES:
        raise ValueError(f"host not allowlisted: {host}")
    return FAKE_HTTP_PAGES[host]


# ---------- 沙箱只读文件 ----------


@dataclass
class Workspace:
    """只读工作区：禁止跳出 root。"""

    root: Path

    def __post_init__(self) -> None:
        self.root = self.root.resolve()
        if not self.root.is_dir():
            raise ValueError("workspace root must be a directory")

    def resolve_safe(self, relative: str) -> Path:
        rel = relative.strip().replace("\\", "/")
        if not rel or rel.startswith("/") or ".." in Path(rel).parts:
            raise ValueError("path escapes workspace or is invalid")
        target = (self.root / rel).resolve()
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("path escapes workspace") from exc
        return target

    def list_files(self, relative_dir: str = ".") -> list[str]:
        base = self.resolve_safe(relative_dir if relative_dir.strip() else ".")
        if not base.is_dir():
            raise ValueError("not a directory")
        names = sorted(
            p.name for p in base.iterdir() if not p.name.startswith(".")
        )
        return names

    def read_file(self, relative_path: str, *, max_chars: int = 2000) -> str:
        path = self.resolve_safe(relative_path)
        if not path.is_file():
            raise ValueError("not a file")
        text = path.read_text(encoding="utf-8")
        if len(text) > max_chars:
            return text[:max_chars] + "\n…(truncated)"
        return text


# ---------- 业务副作用账本（HITL 演示） ----------

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


@dataclass
class SideEffectLedger:
    """记录已执行的副作用，便于断言「拒绝后无退款」。"""

    refunded_orders: set[str] = field(default_factory=set)
    deleted_accounts: set[str] = field(default_factory=set)


def order_lookup(order_id: str) -> dict[str, str]:
    key = order_id.strip().upper()
    if key not in ORDER_DB:
        raise ValueError(f"order not found: {key}")
    return dict(ORDER_DB[key])


def refund_order(order_id: str, ledger: SideEffectLedger) -> str:
    key = order_id.strip().upper()
    if key not in ORDER_DB:
        raise ValueError(f"order not found: {key}")
    ledger.refunded_orders.add(key)
    return f"refunded {key} amount={ORDER_DB[key]['total']} {ORDER_DB[key]['currency']}"


def get_time_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- Tool Spec 目录 ----------

ToolHandler = Callable[..., Any]


@dataclass(frozen=True)
class ToolSpec:
    """工具规格：名称 / 描述 / JSON Schema 风格 parameters / handler / 风险。"""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler
    risk: str = "safe"  # safe | confirm | blocked
    enabled: bool = True


def build_default_tools(
    workspace: Workspace,
    ledger: SideEffectLedger,
) -> dict[str, ToolSpec]:
    """构建里程碑默认工具集（≥3 个真实能力 + 1 个 confirm + 1 个 blocked）。"""

    def _list_files(relative_dir: str = ".") -> list[str]:
        return workspace.list_files(relative_dir)

    def _read_file(relative_path: str) -> str:
        return workspace.read_file(relative_path)

    def _refund(order_id: str) -> str:
        return refund_order(order_id, ledger)

    def _shell(_cmd: str) -> str:
        raise RuntimeError("shell_exec must never run")

    specs = [
        ToolSpec(
            name="get_time",
            description="返回当前 UTC 时间（ISO8601）。",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            handler=lambda: get_time_iso(),
            risk="safe",
        ),
        ToolSpec(
            name="calculate",
            description="安全计算算术表达式，例如 12*(3+4)。",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "算术表达式"}
                },
                "required": ["expression"],
                "additionalProperties": False,
            },
            handler=lambda expression: safe_calculate(expression),
            risk="safe",
        ),
        ToolSpec(
            name="list_files",
            description="列出沙箱工作区内某目录的文件名。",
            parameters={
                "type": "object",
                "properties": {
                    "relative_dir": {
                        "type": "string",
                        "description": "相对工作区的目录，默认 .",
                    }
                },
                "required": [],
                "additionalProperties": False,
            },
            handler=_list_files,
            risk="safe",
        ),
        ToolSpec(
            name="read_file",
            description="读取沙箱工作区内的文本文件（只读）。",
            parameters={
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": "相对工作区的文件路径",
                    }
                },
                "required": ["relative_path"],
                "additionalProperties": False,
            },
            handler=_read_file,
            risk="safe",
        ),
        ToolSpec(
            name="http_get",
            description="对白名单 host 发起假 HTTP GET，返回正文摘要。",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "https URL"}
                },
                "required": ["url"],
                "additionalProperties": False,
            },
            handler=lambda url: fake_http_get(url),
            risk="safe",
        ),
        ToolSpec(
            name="order_lookup",
            description="按订单号查询订单（只读）。",
            parameters={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "如 ORD-1001"}
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
            handler=lambda order_id: order_lookup(order_id),
            risk="safe",
        ),
        ToolSpec(
            name="refund_order",
            description="对订单发起退款（有副作用，需 HITL 确认）。",
            parameters={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "如 ORD-1001"}
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
            handler=_refund,
            risk="confirm",
        ),
        ToolSpec(
            name="shell_exec",
            description="执行任意 shell（危险，应被永久拦截）。",
            parameters={
                "type": "object",
                "properties": {"cmd": {"type": "string"}},
                "required": ["cmd"],
                "additionalProperties": False,
            },
            handler=_shell,
            risk="blocked",
            enabled=False,
        ),
    ]
    return {s.name: s for s in specs}


def openai_style_tools(specs: dict[str, ToolSpec]) -> list[dict[str, Any]]:
    """导出给 Prompt / MockLLM 的 tools 列表（仅 enabled 且非 blocked）。"""
    out: list[dict[str, Any]] = []
    for spec in specs.values():
        if not spec.enabled or spec.risk == "blocked":
            continue
        out.append(
            {
                "type": "function",
                "function": {
                    "name": spec.name,
                    "description": spec.description,
                    "parameters": spec.parameters,
                },
            }
        )
    return out
