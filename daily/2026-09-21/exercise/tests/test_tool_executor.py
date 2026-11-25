"""Day 43：单轮 Tool Call 执行。"""

from __future__ import annotations

import json

import pytest

from tool_executor import (
    DEMO_TIME_UTC,
    REQUIRED_TOOL_NAMES,
    ToolCall,
    default_registry,
    execute_assistant_tool_calls,
    execute_tool_call,
    extract_tool_calls,
    normalize_text,
    parse_arguments,
    parse_tool_call,
    render_results_markdown,
    safe_calculate,
    stringify_result,
    to_tool_messages,
    tool_calculate,
    tool_get_current_time,
    tool_get_weather,
)


def test_normalize_text() -> None:
    assert normalize_text("  你好\n\n世界  ") == "你好 世界"
    assert normalize_text("a\tb  c") == "a b c"
    assert normalize_text("   ") == ""


def test_parse_arguments() -> None:
    assert parse_arguments(None) == {}
    assert parse_arguments("   ") == {}
    assert parse_arguments('{"city":"Shanghai"}') == {"city": "Shanghai"}
    assert parse_arguments({"city": "Beijing"}) == {"city": "Beijing"}
    # 浅拷贝：改返回值不影响入参
    src = {"a": 1}
    out = parse_arguments(src)
    out["a"] = 2
    assert src["a"] == 1
    with pytest.raises(ValueError, match="arguments"):
        parse_arguments("[1, 2]")
    with pytest.raises(ValueError, match="arguments"):
        parse_arguments("{bad")


def test_parse_and_extract_tool_calls() -> None:
    raw = {
        "id": " call_1 ",
        "type": "function",
        "function": {
            "name": " get_weather ",
            "arguments": '{"city": "Shanghai"}',
        },
    }
    call = parse_tool_call(raw)
    assert call == ToolCall(id="call_1", name="get_weather", arguments={"city": "Shanghai"})

    # type 缺省视为 function
    call2 = parse_tool_call(
        {
            "id": "call_2",
            "function": {"name": "calculate", "arguments": "{}"},
        }
    )
    assert call2.name == "calculate"

    with pytest.raises(ValueError, match="id"):
        parse_tool_call({"id": "  ", "function": {"name": "x", "arguments": "{}"}})
    with pytest.raises(ValueError, match="function"):
        parse_tool_call({"id": "c", "type": "tool", "function": {"name": "x", "arguments": "{}"}})
    with pytest.raises(ValueError, match="name"):
        parse_tool_call({"id": "c", "function": {"name": "  ", "arguments": "{}"}})

    message = {"role": "assistant", "tool_calls": [raw]}
    calls = extract_tool_calls(message)
    assert len(calls) == 1
    assert calls[0].id == "call_1"
    assert extract_tool_calls({"role": "assistant"}) == []
    assert extract_tool_calls({"role": "assistant", "tool_calls": None}) == []
    with pytest.raises(ValueError, match="tool_calls"):
        extract_tool_calls({"tool_calls": {"id": "x"}})


def test_safe_calculate() -> None:
    assert safe_calculate("12 * (3 + 4)") == 84
    assert safe_calculate("  2**3  ") == 8
    assert safe_calculate("-5 + 2") == -3
    assert safe_calculate("7 // 2") == 3
    with pytest.raises(ValueError, match="expression"):
        safe_calculate("   ")
    with pytest.raises(ValueError, match="unsafe"):
        safe_calculate("__import__('os').system('ls')")
    with pytest.raises(ValueError, match="unsafe"):
        safe_calculate("a + 1")


def test_mock_tools() -> None:
    w = tool_get_weather("Shanghai")
    assert w["city"] == "Shanghai"
    assert w["unit"] == "celsius"
    assert w["temp"] == 28
    assert w["condition"] == "sunny"

    f = tool_get_weather("Paris", unit="FAHRENHEIT")
    assert f["unit"] == "fahrenheit"
    assert f["temp"] == 68  # 20C → 68F
    assert f["condition"] == "cloudy"

    with pytest.raises(ValueError, match="city"):
        tool_get_weather("  ")
    with pytest.raises(ValueError, match="unit"):
        tool_get_weather("Shanghai", unit="kelvin")

    calc = tool_calculate("10/2")
    assert calc == {"expression": "10/2", "result": 5}

    t = tool_get_current_time(" Asia/Shanghai ")
    assert t == {"timezone": "Asia/Shanghai", "datetime": DEMO_TIME_UTC}
    with pytest.raises(ValueError, match="timezone"):
        tool_get_current_time("  ")


def test_registry_and_stringify() -> None:
    reg = default_registry()
    assert set(reg) == set(REQUIRED_TOOL_NAMES)
    assert stringify_result("plain") == "plain"
    assert stringify_result({"a": 1}) == '{"a":1}'
    assert stringify_result([1, 2]) == "[1,2]"
    assert stringify_result(True) == "true"
    assert stringify_result(3) == "3"
    assert stringify_result(None) == "null"


def test_execute_tool_call_success_and_failure() -> None:
    ok = execute_tool_call(
        ToolCall(id="c1", name="get_weather", arguments={"city": "Shanghai"})
    )
    assert ok.ok is True
    assert ok.tool_call_id == "c1"
    assert ok.name == "get_weather"
    payload = json.loads(ok.content)
    assert payload["temp"] == 28

    calc = execute_tool_call(
        ToolCall(id="c2", name="calculate", arguments={"expression": "1+2*3"})
    )
    assert calc.ok is True
    assert json.loads(calc.content)["result"] == 7

    unknown = execute_tool_call(ToolCall(id="c3", name="launch_missile", arguments={}))
    assert unknown.ok is False
    assert unknown.content.startswith("ERROR:")
    assert "unknown" in unknown.content.lower()

    bad = execute_tool_call(
        ToolCall(id="c4", name="calculate", arguments={"expression": "os.system"})
    )
    assert bad.ok is False
    assert bad.content.startswith("ERROR:")


def test_batch_and_messages_and_markdown() -> None:
    message = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_a",
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "arguments": '{"timezone": "UTC"}',
                },
            },
            {
                "id": "call_b",
                "type": "function",
                "function": {
                    "name": "nope",
                    "arguments": "{}",
                },
            },
        ],
    }
    results = execute_assistant_tool_calls(message)
    assert len(results) == 2
    assert results[0].ok is True
    assert results[1].ok is False

    msgs = to_tool_messages(results)
    assert msgs[0] == {
        "role": "tool",
        "tool_call_id": "call_a",
        "content": results[0].content,
    }
    assert msgs[1]["role"] == "tool"
    assert msgs[1]["tool_call_id"] == "call_b"
    assert "name" not in msgs[0]

    md = render_results_markdown(results)
    lines = md.splitlines()
    assert lines[0] == "# Tool Execution"
    assert "## get_current_time (ok)" in lines
    assert "## nope (ERROR)" in lines
    assert any(line.startswith("id：") for line in lines)
    assert any(line.startswith("content：") for line in lines)
