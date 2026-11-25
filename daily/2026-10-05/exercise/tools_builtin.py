"""Day 52 附带：内置工具（lookup + calculate），已给齐。

与 Day46 tools.py 同能力；今天主战场在 mini_framework.py。
只用标准库。
"""

from __future__ import annotations

import ast
import json
import operator
from typing import Any, Callable

ToolHandler = Callable[..., Any]

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
    text = normalize_text(expression)
    if not text:
        raise ValueError("expression must be non-empty")
    tree = ast.parse(text, mode="eval")
    return _eval_ast(tree)


def lookup(key: str) -> str:
    cleaned = normalize_text(key)
    if not cleaned:
        raise ValueError("key must be non-empty")
    if cleaned not in LOOKUP_KB:
        raise KeyError(f"unknown key: {cleaned}")
    return LOOKUP_KB[cleaned]


def calculate(expression: str) -> str:
    value = safe_calculate(expression)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def lookup_tool_meta() -> dict[str, Any]:
    return {
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
        "handler": lookup,
    }


def calculate_tool_meta() -> dict[str, Any]:
    return {
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
        "handler": calculate,
    }


def builtin_tool_metas() -> list[dict[str, Any]]:
    """返回固定顺序的内置工具元数据（供 Registry 注册）。"""
    return [lookup_tool_meta(), calculate_tool_meta()]


def format_tool_result(value: Any) -> str:
    """把工具返回值压成 observation 字符串。"""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)
