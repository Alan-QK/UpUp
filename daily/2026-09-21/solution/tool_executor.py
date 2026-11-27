"""Day 43 参考实现：单轮 Tool Call 执行器。"""

from __future__ import annotations

import ast
import json
import operator
from dataclasses import dataclass
from typing import Any, Callable

ToolHandler = Callable[..., Any]

REQUIRED_TOOL_NAMES: tuple[str, ...] = (
    "get_weather",
    "calculate",
    "get_current_time",
)

DEMO_TIME_UTC = "2026-09-21T02:00:00+00:00"

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
    """一条已解析的工具调用。"""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    """一条工具执行结果（成功或失败）。"""

    tool_call_id: str
    name: str
    content: str
    ok: bool


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白（含换行）压成单个空格。"""
    return " ".join(text.split())


def parse_arguments(arguments: str | dict[str, Any] | None) -> dict[str, Any]:
    """把模型侧 arguments 解析为 dict。"""
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
    """解析一条 OpenAI 风格 tool_call。"""
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

    arguments = parse_arguments(function.get("arguments"))
    return ToolCall(id=call_id, name=name, arguments=arguments)


def extract_tool_calls(assistant_message: dict[str, Any]) -> list[ToolCall]:
    """从 assistant 消息提取并解析全部 tool_calls。"""
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
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        return _ALLOWED_BINOPS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_UNARYOPS:
            raise ValueError("unsafe expression unary")
        return _ALLOWED_UNARYOPS[op_type](_eval_ast(node.operand))
    raise ValueError("unsafe expression node")


def safe_calculate(expression: str) -> float | int:
    """安全求值算术表达式。"""
    text = normalize_text(expression)
    if not text:
        raise ValueError("expression must be non-empty")
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"unsafe expression syntax: {exc}") from exc
    try:
        value = _eval_ast(tree)
    except ValueError:
        raise
    except Exception as exc:  # pragma: no cover - 保守兜底
        raise ValueError(f"unsafe expression: {exc}") from exc
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def tool_get_weather(city: str, unit: str = "celsius") -> dict[str, Any]:
    """Mock 天气：不访问网络。"""
    city_name = normalize_text(city)
    if not city_name:
        raise ValueError("city must be non-empty")
    unit_name = normalize_text(unit).lower()
    if unit_name not in {"celsius", "fahrenheit"}:
        raise ValueError("unit must be celsius or fahrenheit")

    if city_name.lower() == "shanghai":
        temp_c = 28
        condition = "sunny"
    else:
        temp_c = 20
        condition = "cloudy"

    temp: float | int = temp_c
    if unit_name == "fahrenheit":
        temp = int(temp_c * 9 / 5 + 32)

    return {
        "city": city_name,
        "unit": unit_name,
        "temp": temp,
        "condition": condition,
    }


def tool_calculate(expression: str) -> dict[str, Any]:
    """封装 safe_calculate。"""
    result = safe_calculate(expression)
    return {"expression": expression, "result": result}


def tool_get_current_time(timezone: str = "UTC") -> dict[str, Any]:
    """返回演示时间。"""
    tz = normalize_text(timezone)
    if not tz:
        raise ValueError("timezone must be non-empty")
    return {"timezone": tz, "datetime": DEMO_TIME_UTC}


def default_registry() -> dict[str, ToolHandler]:
    """返回 name → handler 映射。"""
    return {
        "get_weather": tool_get_weather,
        "calculate": tool_calculate,
        "get_current_time": tool_get_current_time,
    }


def stringify_result(value: Any) -> str:
    """把执行结果变成 content 字符串。"""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, bool, int, float)) or value is None:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def execute_tool_call(
    call: ToolCall,
    registry: dict[str, ToolHandler] | None = None,
) -> ToolResult:
    """执行单条 ToolCall。"""
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
    """提取并执行 assistant 消息中的全部 tool_calls。"""
    calls = extract_tool_calls(assistant_message)
    return [execute_tool_call(call, registry=registry) for call in calls]


def to_tool_messages(results: list[ToolResult]) -> list[dict[str, Any]]:
    """把 ToolResult 列表转成 Chat Completions 的 tool 消息列表。"""
    return [
        {
            "role": "tool",
            "tool_call_id": item.tool_call_id,
            "content": item.content,
        }
        for item in results
    ]


def render_results_markdown(results: list[ToolResult]) -> str:
    """渲染执行结果摘要。"""
    lines = ["# Tool Execution"]
    for item in results:
        status = "ok" if item.ok else "ERROR"
        lines.extend(
            [
                f"## {item.name} ({status})",
                f"id：{item.tool_call_id}",
                f"content：{item.content}",
            ]
        )
    return "\n".join(lines)
