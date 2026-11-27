"""Day 46 附带：Loop 练习用工具箱（lookup + calculate）。

Schema + 安全执行器已给齐；练习主战场在 agent_loop.py。
只用标准库。
"""

from __future__ import annotations

import ast
import json
import operator
from typing import Any, Callable

ToolHandler = Callable[..., Any]

LOOP_TOOL_NAMES: tuple[str, ...] = ("lookup", "calculate")

# 固定知识表：保证多步 Demo / 单测可复现
LOOKUP_KB: dict[str, str] = {
    "alpha": "7",
    "beta": "3",
    "france_capital": "Paris",
    "paris_country": "France",
}

_ALLOWED_BINOPS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED_UNARYOPS: dict[type, Any] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def build_lookup_tool() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "lookup",
            "description": (
                "从本地知识表查询键对应的字符串值。"
                "当需要已知事实（如 alpha、france_capital）时使用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "知识表中的键名，如 alpha、france_capital",
                    },
                },
                "required": ["key"],
            },
        },
    }


def build_calculate_tool() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": (
                "计算算术表达式（仅支持数字与 + - * / // % ** 与括号）。"
                "需要精确数值时使用，不要心算。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "算术表达式，例如 7*3 或 (1+2)*4",
                    },
                },
                "required": ["expression"],
            },
        },
    }


def loop_toolkit() -> list[dict[str, Any]]:
    """返回固定顺序的工具 Schema 列表。"""
    return [build_lookup_tool(), build_calculate_tool()]


def _eval_ast(node: ast.AST) -> float | int:
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
        return _ALLOWED_UNARYOPS[type(node.op)](_eval_ast(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        return _ALLOWED_BINOPS[type(node.op)](left, right)
    raise ValueError("unsupported expression")


def safe_calculate(expression: str) -> float | int:
    """AST 白名单求值；禁止 eval。"""
    text = normalize_text(expression)
    if not text:
        raise ValueError("expression must be non-empty")
    tree = ast.parse(text, mode="eval")
    return _eval_ast(tree)


def lookup(key: str) -> str:
    """查知识表；未知键抛 ValueError。"""
    normalized = normalize_text(key)
    if not normalized:
        raise ValueError("key must be non-empty")
    if normalized not in LOOKUP_KB:
        raise ValueError(f"unknown key: {normalized}")
    return LOOKUP_KB[normalized]


def parse_tool_call(raw: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    """解析单条 tool_call → (id, name, arguments)。"""
    if not isinstance(raw, dict):
        raise ValueError("tool_call must be a dict")
    call_id = normalize_text(str(raw.get("id", "")))
    if not call_id:
        raise ValueError("tool_call id must be non-empty")
    fn = raw.get("function")
    if not isinstance(fn, dict):
        raise ValueError("tool_call.function must be a dict")
    name = normalize_text(str(fn.get("name", "")))
    if not name:
        raise ValueError("tool name must be non-empty")
    args_raw = fn.get("arguments", "{}")
    if isinstance(args_raw, dict):
        args = args_raw
    elif isinstance(args_raw, str):
        try:
            parsed = json.loads(args_raw) if args_raw.strip() else {}
        except json.JSONDecodeError as exc:
            raise ValueError("arguments must be valid JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("arguments JSON must be an object")
        args = parsed
    else:
        raise ValueError("arguments must be str or dict")
    return call_id, name, args


_HANDLERS: dict[str, ToolHandler] = {
    "lookup": lambda key: lookup(str(key)),
    "calculate": lambda expression: safe_calculate(str(expression)),
}


def execute_one(raw: dict[str, Any]) -> dict[str, Any]:
    """执行单条 tool_call，始终返回 role=tool 消息（失败则 ERROR: 前缀）。"""
    try:
        call_id, name, args = parse_tool_call(raw)
    except ValueError as exc:
        return {
            "role": "tool",
            "tool_call_id": "invalid",
            "content": f"ERROR: {exc}",
        }

    handler = _HANDLERS.get(name)
    if handler is None:
        return {
            "role": "tool",
            "tool_call_id": call_id,
            "content": f"ERROR: unknown tool: {name}",
        }

    try:
        if name == "lookup":
            if "key" not in args:
                raise ValueError("missing key")
            value = handler(key=args["key"])
            payload = {"key": normalize_text(str(args["key"])), "value": value}
        elif name == "calculate":
            if "expression" not in args:
                raise ValueError("missing expression")
            result = handler(expression=args["expression"])
            payload = {
                "expression": normalize_text(str(args["expression"])),
                "result": result,
            }
        else:
            raise ValueError(f"unhandled tool: {name}")
        return {
            "role": "tool",
            "tool_call_id": call_id,
            "content": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        }
    except Exception as exc:  # noqa: BLE001 - 工具失败也要回填
        return {
            "role": "tool",
            "tool_call_id": call_id,
            "content": f"ERROR: {exc}",
        }


def execute_assistant_tools(assistant_message: dict[str, Any]) -> list[dict[str, Any]]:
    """按顺序执行 assistant.tool_calls，返回 role=tool 消息列表。"""
    if not isinstance(assistant_message, dict):
        raise ValueError("assistant_message must be a dict")
    raw_calls = assistant_message.get("tool_calls")
    if not isinstance(raw_calls, list) or not raw_calls:
        raise ValueError("assistant has no tool_calls")
    return [execute_one(item) for item in raw_calls]
