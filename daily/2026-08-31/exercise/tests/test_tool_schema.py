"""Day 28：从函数到 JSON Schema · tool schema。"""

from __future__ import annotations

from typing import Literal

import pytest

from tool_schema import (
    annotation_to_json_schema,
    function_description,
    function_to_parameters_schema,
    function_to_tool_schema,
    is_optional_annotation,
    parse_args_descriptions,
    tools_from_functions,
    unwrap_optional,
)


def get_weather(
    city: str,
    unit: Literal["celsius", "fahrenheit"] = "celsius",
    detail: bool = False,
) -> str:
    """查询城市天气。

    Args:
        city: 城市名
        unit: 温度单位
        detail: 是否返回详细预报
    """
    return f"{city}:{unit}:{detail}"


def add(a: int, b: int) -> int:
    """两数相加。"""
    return a + b


def maybe_tag(text: str, tag: str | None = None) -> str:
    """可选打标签。"""
    return text if tag is None else f"{tag}:{text}"


def search(query: str, limit: int = 10) -> list[str]:
    """搜索文档。

    Args:
        query: 检索词
        limit: 返回条数上限
    """
    return [query] * limit


class Demo:
    def method(self, x: int) -> int:
        """实例方法应跳过 self。"""
        return x


def test_is_optional_and_unwrap() -> None:
    assert is_optional_annotation(str | None) is True
    assert is_optional_annotation(str) is False
    assert unwrap_optional(str | None) is str
    assert unwrap_optional(int) is int
    with pytest.raises(ValueError, match="union"):
        unwrap_optional(str | int | None)


def test_annotation_primitives_and_literal() -> None:
    assert annotation_to_json_schema(str) == {"type": "string"}
    assert annotation_to_json_schema(int) == {"type": "integer"}
    assert annotation_to_json_schema(float) == {"type": "number"}
    assert annotation_to_json_schema(bool) == {"type": "boolean"}
    assert annotation_to_json_schema(list[str]) == {
        "type": "array",
        "items": {"type": "string"},
    }
    assert annotation_to_json_schema(dict) == {"type": "object"}
    assert annotation_to_json_schema(Literal["celsius", "fahrenheit"]) == {
        "type": "string",
        "enum": ["celsius", "fahrenheit"],
    }
    # Optional 剥掉后按内层类型
    assert annotation_to_json_schema(str | None) == {"type": "string"}


def test_annotation_errors() -> None:
    import inspect

    with pytest.raises(ValueError, match="annotation"):
        annotation_to_json_schema(inspect.Parameter.empty)
    with pytest.raises(ValueError, match="unsupported"):
        annotation_to_json_schema(object)


def test_parse_args_and_description() -> None:
    doc = get_weather.__doc__
    args = parse_args_descriptions(doc)
    assert args["city"] == "城市名"
    assert args["unit"] == "温度单位"
    assert args["detail"] == "是否返回详细预报"
    assert parse_args_descriptions(None) == {}
    assert parse_args_descriptions("只有一行说明") == {}
    assert function_description(get_weather) == "查询城市天气。"
    assert function_description(add) == "两数相加。"

    def no_doc(x: int) -> int:
        return x

    assert function_description(no_doc) == ""


def test_function_to_parameters_schema_weather() -> None:
    params = function_to_parameters_schema(get_weather)
    assert params["type"] == "object"
    assert list(params["properties"].keys()) == ["city", "unit", "detail"]
    assert params["properties"]["city"] == {
        "type": "string",
        "description": "城市名",
    }
    assert params["properties"]["unit"] == {
        "type": "string",
        "enum": ["celsius", "fahrenheit"],
        "description": "温度单位",
    }
    assert params["properties"]["detail"]["type"] == "boolean"
    assert params["required"] == ["city"]


def test_required_rules() -> None:
    params = function_to_parameters_schema(add)
    assert params["required"] == ["a", "b"]
    assert "description" not in params["properties"]["a"]

    optional_params = function_to_parameters_schema(maybe_tag)
    assert optional_params["required"] == ["text"]
    assert "tag" not in optional_params["required"]
    assert optional_params["properties"]["tag"] == {"type": "string"}


def test_skip_self_and_reject_variadic() -> None:
    params = function_to_parameters_schema(Demo.method)
    assert list(params["properties"].keys()) == ["x"]
    assert params["required"] == ["x"]

    def bad_star(*args: str) -> None:
        return None

    with pytest.raises(ValueError, match="variadic"):
        function_to_parameters_schema(bad_star)

    def bad_kw(**kwargs: str) -> None:
        return None

    with pytest.raises(ValueError, match="variadic"):
        function_to_parameters_schema(bad_kw)

    def missing_ann(x) -> None:  # noqa: ANN001
        return None

    with pytest.raises(ValueError, match="annotation"):
        function_to_parameters_schema(missing_ann)


def test_function_to_tool_schema() -> None:
    tool = function_to_tool_schema(get_weather)
    assert tool["type"] == "function"
    assert tool["function"]["name"] == "get_weather"
    assert tool["function"]["description"] == "查询城市天气。"
    assert tool["function"]["parameters"]["required"] == ["city"]

    renamed = function_to_tool_schema(get_weather, name="weather_query", description="自定义")
    assert renamed["function"]["name"] == "weather_query"
    assert renamed["function"]["description"] == "自定义"

    with pytest.raises(ValueError, match="name"):
        function_to_tool_schema(get_weather, name="bad-name")
    with pytest.raises(TypeError):
        function_to_tool_schema(123)  # type: ignore[arg-type]


def test_tools_from_functions() -> None:
    assert tools_from_functions() == []
    tools = tools_from_functions(add, search)
    assert [t["function"]["name"] for t in tools] == ["add", "search"]
    assert tools[1]["function"]["parameters"]["properties"]["limit"]["type"] == "integer"

    with pytest.raises(ValueError, match="duplicate"):
        tools_from_functions(add, add)
