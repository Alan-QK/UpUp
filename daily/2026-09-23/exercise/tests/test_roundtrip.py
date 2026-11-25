"""Day 44：工具结果回填多轮。"""

from __future__ import annotations

import copy

import pytest

from roundtrip import (
    RoundTripResult,
    ScriptedChat,
    build_messages_after_tools,
    extract_tool_call_ids,
    finalize_content,
    has_tool_calls,
    normalize_text,
    render_roundtrip_markdown,
    run_tool_roundtrip,
    validate_tool_followup,
    validate_tool_message,
)


def _assistant_tools() -> dict:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": " call_a ",
                "type": "function",
                "function": {"name": "get_weather", "arguments": '{"city":"Shanghai"}'},
            },
            {
                "id": "call_b",
                "type": "function",
                "function": {"name": "calculate", "arguments": '{"expression":"1+2"}'},
            },
        ],
    }


def test_normalize_text() -> None:
    assert normalize_text("  你好\n\n世界  ") == "你好 世界"
    assert normalize_text("a\tb  c") == "a b c"
    assert normalize_text("   ") == ""


def test_has_tool_calls_and_ids() -> None:
    assert has_tool_calls(_assistant_tools()) is True
    assert has_tool_calls({"role": "assistant", "content": "hi"}) is False
    assert has_tool_calls({"role": "assistant", "tool_calls": []}) is False
    assert has_tool_calls({"role": "assistant", "tool_calls": None}) is False
    assert has_tool_calls("nope") is False  # type: ignore[arg-type]

    assert extract_tool_call_ids(_assistant_tools()) == ["call_a", "call_b"]
    assert extract_tool_call_ids({"role": "assistant"}) == []

    with pytest.raises(ValueError, match="id"):
        extract_tool_call_ids(
            {
                "role": "assistant",
                "tool_calls": [{"id": "  ", "function": {"name": "x", "arguments": "{}"}}],
            }
        )
    with pytest.raises(ValueError, match="dict"):
        extract_tool_call_ids({"role": "assistant", "tool_calls": ["bad"]})


def test_validate_tool_message() -> None:
    validate_tool_message({"role": "tool", "tool_call_id": "c1", "content": "ok"})
    validate_tool_message({"role": "tool", "tool_call_id": "c1", "content": ""})
    with pytest.raises(ValueError, match="role"):
        validate_tool_message({"role": "assistant", "tool_call_id": "c1", "content": "x"})
    with pytest.raises(ValueError, match="tool_call_id"):
        validate_tool_message({"role": "tool", "tool_call_id": "  ", "content": "x"})
    with pytest.raises(ValueError, match="content"):
        validate_tool_message({"role": "tool", "tool_call_id": "c1", "content": 1})


def test_validate_tool_followup_ok_and_errors() -> None:
    assistant = _assistant_tools()
    tools = [
        {"role": "tool", "tool_call_id": "call_a", "content": "{}"},
        {"role": "tool", "tool_call_id": "call_b", "content": "ERROR: boom"},
    ]
    validate_tool_followup(assistant, tools)

    with pytest.raises(ValueError, match="no tool_calls"):
        validate_tool_followup({"role": "assistant", "content": "x"}, tools)

    with pytest.raises(ValueError, match="count"):
        validate_tool_followup(assistant, tools[:1])

    swapped = [
        {"role": "tool", "tool_call_id": "call_b", "content": "{}"},
        {"role": "tool", "tool_call_id": "call_a", "content": "{}"},
    ]
    with pytest.raises(ValueError, match="mismatch"):
        validate_tool_followup(assistant, swapped)


def test_build_messages_after_tools_is_pure() -> None:
    history = [{"role": "user", "content": "hi"}]
    history_snapshot = copy.deepcopy(history)
    assistant = _assistant_tools()
    tools = [
        {"role": "tool", "tool_call_id": "call_a", "content": '{"temp":28}'},
        {"role": "tool", "tool_call_id": "call_b", "content": '{"result":3}'},
    ]
    tools_snapshot = copy.deepcopy(tools)

    out = build_messages_after_tools(history, assistant, tools)
    assert len(out) == 4
    assert out[0] == {"role": "user", "content": "hi"}
    assert out[1]["tool_calls"][0]["id"] == " call_a "
    assert out[2]["tool_call_id"] == "call_a"
    assert out[3]["content"] == '{"result":3}'

    # 纯度：改返回值不影响入参
    out[0]["content"] = "mutated"
    out[2]["content"] = "mutated-tool"
    assert history == history_snapshot
    assert tools == tools_snapshot

    with pytest.raises(ValueError, match="history"):
        build_messages_after_tools("bad", assistant, tools)  # type: ignore[arg-type]


def test_finalize_content() -> None:
    assert finalize_content({"role": "assistant", "content": "你好"}) == "你好"
    assert finalize_content({"role": "assistant", "content": None}) == ""
    with pytest.raises(ValueError, match="tool_calls"):
        finalize_content(_assistant_tools())
    with pytest.raises(ValueError, match="content"):
        finalize_content({"role": "assistant", "content": 123})


def test_run_tool_roundtrip_without_tools() -> None:
    history = [{"role": "user", "content": "1+1?"}]
    chat = ScriptedChat([{"role": "assistant", "content": "2"}])
    result = run_tool_roundtrip(history, chat)
    assert isinstance(result, RoundTripResult)
    assert result.used_tools is False
    assert result.tool_messages == []
    assert result.final_content == "2"
    assert len(result.messages) == 2
    assert len(chat.calls) == 1
    assert chat.calls[0] == history


def test_run_tool_roundtrip_with_tools() -> None:
    history = [{"role": "user", "content": "上海热不热？算 1+2"}]
    first = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_w",
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"city": "Shanghai"}',
                },
            },
            {
                "id": "call_c",
                "type": "function",
                "function": {
                    "name": "calculate",
                    "arguments": '{"expression": "1+2"}',
                },
            },
        ],
    }
    second = {"role": "assistant", "content": "约 28°C；1+2=3。"}
    chat = ScriptedChat([first, second])

    result = run_tool_roundtrip(history, chat)
    assert result.used_tools is True
    assert len(result.tool_messages) == 2
    assert result.tool_messages[0]["tool_call_id"] == "call_w"
    assert "28" in result.tool_messages[0]["content"]
    assert '"result":3' in result.tool_messages[1]["content"].replace(" ", "")
    assert result.final_content == "约 28°C；1+2=3。"
    assert result.messages[-1]["content"] == result.final_content

    # 第二次请求必须已经带上 assistant + tool*
    assert len(chat.calls) == 2
    second_input = chat.calls[1]
    assert second_input[0] == history[0]
    assert second_input[1]["tool_calls"][0]["id"] == "call_w"
    assert second_input[2]["role"] == "tool"
    assert second_input[3]["role"] == "tool"


def test_run_tool_roundtrip_rejects_second_tool_calls() -> None:
    history = [{"role": "user", "content": "再算一次"}]
    first = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "calculate", "arguments": '{"expression": "1"}'},
            }
        ],
    }
    again = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_2",
                "type": "function",
                "function": {"name": "calculate", "arguments": '{"expression": "2"}'},
            }
        ],
    }
    chat = ScriptedChat([first, again])
    with pytest.raises(ValueError, match="tool_calls"):
        run_tool_roundtrip(history, chat)


def test_custom_execute_and_markdown() -> None:
    history = [{"role": "user", "content": "x"}]
    first = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_x",
                "type": "function",
                "function": {"name": "noop", "arguments": "{}"},
            }
        ],
    }
    second = {"role": "assistant", "content": "done"}
    chat = ScriptedChat([first, second])

    def fake_execute(assistant_message: dict) -> list[dict]:
        assert assistant_message["tool_calls"][0]["id"] == "call_x"
        return [{"role": "tool", "tool_call_id": "call_x", "content": "CUSTOM"}]

    result = run_tool_roundtrip(history, chat, execute=fake_execute)
    assert result.tool_messages[0]["content"] == "CUSTOM"

    md = render_roundtrip_markdown(result)
    lines = md.splitlines()
    assert lines[0] == "# Tool Roundtrip"
    assert "used_tools：yes" in lines
    assert "tool_count：1" in lines
    assert "## Final" in lines
    assert "done" in lines
    assert "- call_x: CUSTOM" in lines
