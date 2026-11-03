"""Day 42：Tool Schema 设计。"""

from __future__ import annotations

import copy

import pytest

from tool_design import (
    REQUIRED_TOOL_NAMES,
    assert_unique_names,
    build_calculate_tool,
    build_get_current_time_tool,
    build_get_weather_tool,
    check_design_quality,
    default_toolkit,
    normalize_text,
    render_toolkit_markdown,
    toolkit_names,
    tools_payload,
    validate_parameters_schema,
    validate_tool_name,
    validate_tool_schema,
)


def test_normalize_text() -> None:
    assert normalize_text("  你好\n\n世界  ") == "你好 世界"
    assert normalize_text("a\tb  c") == "a b c"
    assert normalize_text("   ") == ""


def test_validate_tool_name() -> None:
    assert validate_tool_name(" get_weather ") == "get_weather"
    assert validate_tool_name("calculate") == "calculate"
    with pytest.raises(ValueError, match="name"):
        validate_tool_name("GetWeather")
    with pytest.raises(ValueError, match="name"):
        validate_tool_name("ab")
    with pytest.raises(ValueError, match="name"):
        validate_tool_name("bad-name")
    with pytest.raises(ValueError, match="name"):
        validate_tool_name("1weather")


def test_validate_parameters_schema_ok_and_required() -> None:
    validate_parameters_schema(
        {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "unit": {"type": "string"},
            },
            "required": ["city"],
        }
    )
    with pytest.raises(ValueError, match="object"):
        validate_parameters_schema({"type": "array", "properties": {}})
    with pytest.raises(ValueError, match="properties"):
        validate_parameters_schema({"type": "object", "properties": "nope"})
    with pytest.raises(ValueError, match="missing"):
        validate_parameters_schema(
            {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["missing_field"],
            }
        )
    with pytest.raises(ValueError, match="type"):
        validate_parameters_schema(
            {
                "type": "object",
                "properties": {"city": {"description": "no type"}},
            }
        )


def test_validate_tool_schema_structure() -> None:
    ok = build_get_weather_tool()
    validate_tool_schema(ok)

    bad = copy.deepcopy(ok)
    bad["type"] = "tool"
    with pytest.raises(ValueError, match="function"):
        validate_tool_schema(bad)

    bad2 = copy.deepcopy(ok)
    bad2["function"]["description"] = "   "
    with pytest.raises(ValueError, match="description"):
        validate_tool_schema(bad2)

    bad3 = copy.deepcopy(ok)
    bad3["function"]["name"] = "Bad Name"
    with pytest.raises(ValueError, match="name"):
        validate_tool_schema(bad3)


def test_check_design_quality_rules() -> None:
    tool = build_calculate_tool()
    check_design_quality(tool)

    short = copy.deepcopy(tool)
    short["function"]["description"] = "用于计算"  # < 20 after normalize? 用于计算 = 4 chars
    with pytest.raises(ValueError, match="short"):
        check_design_quality(short)

    no_hint = copy.deepcopy(tool)
    no_hint["function"]["description"] = (
        "这是一个普通的算术小助手工具定义文本，仅作占位说明而已"
    )
    with pytest.raises(ValueError, match="hint"):
        check_design_quality(no_hint)

    no_prop_desc = copy.deepcopy(tool)
    del no_prop_desc["function"]["parameters"]["properties"]["expression"]["description"]
    with pytest.raises(ValueError, match="description"):
        check_design_quality(no_prop_desc)

    empty_props = copy.deepcopy(tool)
    empty_props["function"]["parameters"]["properties"] = {}
    empty_props["function"]["parameters"]["required"] = []
    empty_props["function"]["description"] = (
        "当用户需要一个占位工具但没有任何参数时请不要这样设计"
    )
    with pytest.raises(ValueError, match="properties"):
        check_design_quality(empty_props)


def test_build_get_weather_tool() -> None:
    tool = build_get_weather_tool()
    check_design_quality(tool)
    fn = tool["function"]
    assert fn["name"] == "get_weather"
    props = fn["parameters"]["properties"]
    assert set(props) == {"city", "unit"}
    assert props["unit"]["enum"] == ["celsius", "fahrenheit"]
    assert fn["parameters"]["required"] == ["city"]


def test_build_calculate_tool() -> None:
    tool = build_calculate_tool()
    check_design_quality(tool)
    fn = tool["function"]
    assert fn["name"] == "calculate"
    assert set(fn["parameters"]["properties"]) == {"expression"}
    assert fn["parameters"]["required"] == ["expression"]


def test_build_get_current_time_tool() -> None:
    tool = build_get_current_time_tool()
    check_design_quality(tool)
    fn = tool["function"]
    assert fn["name"] == "get_current_time"
    assert "timezone" in fn["parameters"]["properties"]
    required = fn["parameters"].get("required", [])
    assert required == []
    assert "timezone" not in required


def test_default_toolkit_and_unique() -> None:
    tools = default_toolkit()
    assert toolkit_names(tools) == list(REQUIRED_TOOL_NAMES)
    assert_unique_names(tools)

    dup = [build_calculate_tool(), build_calculate_tool()]
    with pytest.raises(ValueError, match="duplicate"):
        assert_unique_names(dup)


def test_render_and_payload() -> None:
    tools = default_toolkit()
    md = render_toolkit_markdown(tools)
    lines = md.splitlines()
    assert lines[0] == "# Tool Toolkit"
    assert "## get_weather" in lines
    assert "## calculate" in lines
    assert "## get_current_time" in lines
    assert any(line.startswith("描述：") for line in lines)
    assert any(line.startswith("必填：") for line in lines)
    assert any(line.startswith("参数：") for line in lines)

    payload = tools_payload(tools)
    assert isinstance(payload, list)
    assert payload is not tools
    assert len(payload) == 3
    assert payload[0]["type"] == "function"

    with pytest.raises(ValueError):
        render_toolkit_markdown([])
