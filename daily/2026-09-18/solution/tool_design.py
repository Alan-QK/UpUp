"""参考实现：请先自己完成 exercise/ 再对照。

纯标准库：手写 OpenAI 风格 Tool Schema + 设计质量校验。
"""

from __future__ import annotations

import re
from typing import Any

REQUIRED_TOOL_NAMES: tuple[str, ...] = (
    "get_weather",
    "calculate",
    "get_current_time",
)

_TOOL_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")

_WHEN_HINTS = (
    "当",
    "如果",
    "需要",
    "用于",
    "查询",
    "计算",
    "获取",
    "when",
    "use",
    "need",
)


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白（含换行）压成单个空格。"""
    return " ".join(text.split())


def validate_tool_name(name: str) -> str:
    """校验并返回规范化后的工具名。"""
    if not isinstance(name, str):
        raise ValueError("name must be a string")
    normalized = name.strip()
    if not _TOOL_NAME_RE.fullmatch(normalized):
        raise ValueError(
            "name must match ^[a-z][a-z0-9_]{2,63}$ "
            f"(got {name!r})"
        )
    return normalized


def validate_parameters_schema(parameters: dict[str, Any]) -> None:
    """校验 parameters 对象。"""
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be a dict")
    if parameters.get("type") != "object":
        raise ValueError('parameters.type must be "object"')

    properties = parameters.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("parameters.properties must be a dict")

    for key, schema in properties.items():
        if not isinstance(key, str) or not key:
            raise ValueError("property name must be a non-empty string")
        if not isinstance(schema, dict):
            raise ValueError(f"property {key!r} schema must be a dict")
        prop_type = schema.get("type")
        if not isinstance(prop_type, str) or not prop_type.strip():
            raise ValueError(f"property {key!r} must have a non-empty type")

    if "required" in parameters:
        required = parameters["required"]
        if not isinstance(required, list):
            raise ValueError("parameters.required must be a list")
        for item in required:
            if not isinstance(item, str):
                raise ValueError("required entries must be strings")
            if item not in properties:
                raise ValueError(
                    f"required field {item!r} missing from properties"
                )


def validate_tool_schema(tool: dict[str, Any]) -> None:
    """校验一条 OpenAI 风格 tool 定义。"""
    if not isinstance(tool, dict):
        raise ValueError("tool must be a dict")
    if tool.get("type") != "function":
        raise ValueError('tool.type must be "function"')

    function = tool.get("function")
    if not isinstance(function, dict):
        raise ValueError("tool.function must be a dict")

    validate_tool_name(function.get("name", ""))

    description = function.get("description")
    if not isinstance(description, str) or not normalize_text(description):
        raise ValueError("description must be a non-empty string")

    parameters = function.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be a dict")
    validate_parameters_schema(parameters)


def check_design_quality(tool: dict[str, Any]) -> None:
    """在结构合法之外，再做「设计质量」启发式检查。"""
    validate_tool_schema(tool)
    function = tool["function"]
    description = normalize_text(function["description"])
    if len(description) < 20:
        raise ValueError("description too short (need >= 20 chars)")

    lowered = description.lower()
    if not any(hint in lowered for hint in _WHEN_HINTS):
        raise ValueError("description should hint when to use the tool")

    properties: dict[str, Any] = function["parameters"]["properties"]
    if not properties:
        raise ValueError("properties must not be empty")

    for key, schema in properties.items():
        if "description" not in schema:
            raise ValueError(f"property {key!r} missing description")
        prop_desc = schema["description"]
        if not isinstance(prop_desc, str) or not normalize_text(prop_desc):
            raise ValueError(f"property {key!r} description must not be empty")

        if "enum" in schema:
            enum_values = schema["enum"]
            if not isinstance(enum_values, list) or not enum_values:
                raise ValueError(f"property {key!r} enum must be a non-empty list")
            for value in enum_values:
                if not isinstance(value, (str, int, float, bool)):
                    raise ValueError(
                        f"property {key!r} enum members must be str/int/float/bool"
                    )


def build_get_weather_tool() -> dict[str, Any]:
    """手写 get_weather 工具契约。"""
    tool = {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "查询指定城市的当前天气。"
                "当用户询问气温、是否下雨或穿衣建议且需要真实天气数据时使用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名，如 Shanghai 或 上海",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位；未指定时由实现默认 celsius",
                    },
                },
                "required": ["city"],
            },
        },
    }
    check_design_quality(tool)
    return tool


def build_calculate_tool() -> dict[str, Any]:
    """手写 calculate 工具契约。"""
    tool = {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": (
                "计算算术表达式的结果。"
                "当用户需要加减乘除、括号运算或精确数值计算时使用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "算术表达式字符串，如 12*(3+4)",
                    },
                },
                "required": ["expression"],
            },
        },
    }
    check_design_quality(tool)
    return tool


def build_get_current_time_tool() -> dict[str, Any]:
    """手写 get_current_time 工具契约。"""
    tool = {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": (
                "获取指定时区的当前日期时间。"
                "当用户询问现在几点、今天日期或需要带时区的时间戳时使用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "IANA 时区名，如 Asia/Shanghai；可省略用默认时区",
                    },
                },
                "required": [],
            },
        },
    }
    check_design_quality(tool)
    return tool


def default_toolkit() -> list[dict[str, Any]]:
    """按 REQUIRED_TOOL_NAMES 顺序返回三个工具。"""
    builders = {
        "get_weather": build_get_weather_tool,
        "calculate": build_calculate_tool,
        "get_current_time": build_get_current_time_tool,
    }
    tools = [builders[name]() for name in REQUIRED_TOOL_NAMES]
    assert_unique_names(tools)
    return tools


def toolkit_names(tools: list[dict[str, Any]]) -> list[str]:
    """提取工具名列表。"""
    names: list[str] = []
    for tool in tools:
        validate_tool_schema(tool)
        names.append(validate_tool_name(tool["function"]["name"]))
    return names


def assert_unique_names(tools: list[dict[str, Any]]) -> None:
    """若有重名 → ValueError。"""
    seen: set[str] = set()
    for name in toolkit_names(tools):
        if name in seen:
            raise ValueError(f"duplicate tool name: {name}")
        seen.add(name)


def render_toolkit_markdown(tools: list[dict[str, Any]]) -> str:
    """渲染工具箱摘要 Markdown。"""
    if not tools:
        raise ValueError("tools must not be empty")

    assert_unique_names(tools)
    lines = ["# Tool Toolkit"]
    for tool in tools:
        validate_tool_schema(tool)
        function = tool["function"]
        name = validate_tool_name(function["name"])
        description = normalize_text(function["description"])
        parameters = function["parameters"]
        properties = parameters["properties"]
        required = parameters.get("required") or []
        required_text = ", ".join(required) if required else "（无）"
        params_text = ", ".join(properties.keys()) if properties else "（无）"
        lines.extend(
            [
                f"## {name}",
                f"描述：{description}",
                f"必填：{required_text}",
                f"参数：{params_text}",
            ]
        )
    return "\n".join(lines)


def tools_payload(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """返回可直接塞进 Chat Completions tools 字段的列表。"""
    assert_unique_names(tools)
    for tool in tools:
        validate_tool_schema(tool)
    return list(tools)
