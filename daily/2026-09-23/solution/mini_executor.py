"""Day 44 附带：精简版工具执行器（来自 Day 43 核心能力，接口已给齐）。

练习主战场在 roundtrip.py；本文件无需改 TODO。
"""

from __future__ import annotations

import ast
import json
import operator
from dataclasses import dataclass
from typing import Any, Callable

ToolHandler = Callable[..., Any]

DEMO_TIME_UTC = "2026-09-23T02:00:00+00:00"

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


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    tool_call_id: str
    name: str
    content: str
    ok: bool


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def parse_arguments(arguments: str | dict[str, Any] | None) -> dict[str, Any]:
    if arguments is None:
        return {}
    if isinstance(arguments, dict):
        return dict(arguments)
    if not isinstance(arguments, str):
        raise ValueError("arguments must be str or dict")
    text = arguments.strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid arguments JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("arguments JSON must be an object")
    return data


def parse_tool_call(raw: dict[str, Any]) -> ToolCall:
    if not isinstance(raw, dict):
        raise ValueError("tool_call must be a dict")
    call_id = normalize_text(str(raw.get("id", "")))
    if not call_id:
        raise ValueError("tool_call id must be non-empty")
    call_type = raw.get("type", "function")
    if call_type != "function":
        raise ValueError("tool_call type must be function")
    function = raw.get("function")
    if not isinstance(function, dict):
        raise ValueError("tool_call function must be a dict")
    name = normalize_text(str(function.get("name", "")))
    if not name:
        raise ValueError("tool_call name must be non-empty")
    return ToolCall(id=call_id, name=name, arguments=parse_arguments(function.get("arguments")))


def extract_tool_calls(assistant_message: dict[str, Any]) -> list[ToolCall]:
    if "tool_calls" not in assistant_message or assistant_message["tool_calls"] is None:
        return []
    raw_calls = assistant_message["tool_calls"]
    if not isinstance(raw_calls, list):
        raise ValueError("tool_calls must be a list")
    return [parse_tool_call(item) for item in raw_calls]


def _eval_ast(node: ast.AST) -> float | int:
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_BINOPS:
            raise ValueError("unsafe expression operator")
        return _ALLOWED_BINOPS[op_type](_eval_ast(node.left), _eval_ast(node.right))
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_UNARYOPS:
            raise ValueError("unsafe expression unary")
        return _ALLOWED_UNARYOPS[op_type](_eval_ast(node.operand))
    raise ValueError("unsafe expression node")


def safe_calculate(expression: str) -> float | int:
    text = normalize_text(expression)
    if not text:
        raise ValueError("expression must be non-empty")
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"unsafe expression syntax: {exc}") from exc
    value = _eval_ast(tree)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def tool_get_weather(city: str, unit: str = "celsius") -> dict[str, Any]:
    city_name = normalize_text(city)
    if not city_name:
        raise ValueError("city must be non-empty")
    unit_name = normalize_text(unit).lower()
    if unit_name not in {"celsius", "fahrenheit"}:
        raise ValueError("unit must be celsius or fahrenheit")
    if city_name.lower() == "shanghai":
        temp_c, condition = 28, "sunny"
    else:
        temp_c, condition = 20, "cloudy"
    temp: float | int = temp_c
    if unit_name == "fahrenheit":
        temp = int(temp_c * 9 / 5 + 32)
    return {"city": city_name, "unit": unit_name, "temp": temp, "condition": condition}


def tool_calculate(expression: str) -> dict[str, Any]:
    return {"expression": expression, "result": safe_calculate(expression)}


def tool_get_current_time(timezone: str = "UTC") -> dict[str, Any]:
    tz = normalize_text(timezone)
    if not tz:
        raise ValueError("timezone must be non-empty")
    return {"timezone": tz, "datetime": DEMO_TIME_UTC}


def default_registry() -> dict[str, ToolHandler]:
    return {
        "get_weather": tool_get_weather,
        "calculate": tool_calculate,
        "get_current_time": tool_get_current_time,
    }


def stringify_result(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, bool, int, float)) or value is None:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def execute_tool_call(
    call: ToolCall,
    registry: dict[str, ToolHandler] | None = None,
) -> ToolResult:
    reg = default_registry() if registry is None else registry
    handler = reg.get(call.name)
    if handler is None:
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            content=f"ERROR: unknown tool: {call.name}",
            ok=False,
        )
    try:
        value = handler(**call.arguments)
    except Exception as exc:
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            content=f"ERROR: {exc}",
            ok=False,
        )
    return ToolResult(
        tool_call_id=call.id,
        name=call.name,
        content=stringify_result(value),
        ok=True,
    )


def execute_assistant_tool_calls(
    assistant_message: dict[str, Any],
    registry: dict[str, ToolHandler] | None = None,
) -> list[ToolResult]:
    return [
        execute_tool_call(call, registry=registry)
        for call in extract_tool_calls(assistant_message)
    ]


def to_tool_messages(results: list[ToolResult]) -> list[dict[str, Any]]:
    return [
        {
            "role": "tool",
            "tool_call_id": item.tool_call_id,
            "content": item.content,
        }
        for item in results
    ]
