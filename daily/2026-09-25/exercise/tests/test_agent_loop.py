"""Day 46：ReAct / Agent Loop。"""

from __future__ import annotations

import json

import pytest

from agent_loop import (
    STOP_FINAL,
    STOP_MAX_STEPS,
    ScriptedChat,
    assistant_thought,
    has_tool_calls,
    normalize_text,
    render_trace_markdown,
    run_agent_loop,
    validate_max_steps,
)
from tools import LOOKUP_KB, execute_assistant_tools, loop_toolkit


def _tool_assistant(
    call_id: str,
    name: str,
    arguments: dict,
    content: str | None = "思考中",
) -> dict:
    return {
        "role": "assistant",
        "content": content,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(arguments, ensure_ascii=False),
                },
            }
        ],
    }


def _final(content: str) -> dict:
    return {"role": "assistant", "content": content}


def test_loop_toolkit_order() -> None:
    names = [item["function"]["name"] for item in loop_toolkit()]
    assert names == ["lookup", "calculate"]
    assert "alpha" in LOOKUP_KB


def test_normalize_and_thought_helpers() -> None:
    assert normalize_text("  a\n b\t c  ") == "a b c"
    assert has_tool_calls(_tool_assistant("c1", "lookup", {"key": "alpha"})) is True
    assert has_tool_calls(_final("hi")) is False
    assert has_tool_calls("bad") is False  # type: ignore[arg-type]
    assert assistant_thought(_final("  hello\nworld ")) == "hello world"
    assert assistant_thought({"role": "assistant", "content": None}) == ""
    assert assistant_thought("x") == ""  # type: ignore[arg-type]


def test_validate_max_steps() -> None:
    assert validate_max_steps(3) == 3
    with pytest.raises(ValueError, match="int"):
        validate_max_steps(True)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="int"):
        validate_max_steps(1.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match=">= 1"):
        validate_max_steps(0)


def test_direct_final_answer() -> None:
    chat = ScriptedChat([_final("无需工具，直接说完。")])
    result = run_agent_loop("介绍一下 Agent Loop", chat, max_steps=3)
    assert result.stopped_reason == STOP_FINAL
    assert result.step_count == 1
    assert result.steps[0].kind == "final"
    assert result.final_content == "无需工具，直接说完。"
    assert result.messages[0]["role"] == "system"
    assert result.messages[1]["role"] == "user"
    assert result.messages[-1]["role"] == "assistant"
    assert len(chat.calls) == 1


def test_one_tool_then_final() -> None:
    chat = ScriptedChat(
        [
            _tool_assistant("c1", "lookup", {"key": "france_capital"}, "先查表"),
            _final("法国首都是 Paris。"),
        ]
    )
    result = run_agent_loop("法国首都是哪？", chat)
    assert result.stopped_reason == STOP_FINAL
    assert result.step_count == 2
    assert result.steps[0].kind == "action"
    assert result.steps[1].kind == "final"
    assert len(result.steps[0].observations) == 1
    assert "Paris" in result.steps[0].observations[0]["content"]
    assert result.final_content == "法国首都是 Paris。"
    # 第二轮 chat 入参应已包含 tool 观察
    assert any(m.get("role") == "tool" for m in chat.calls[1])


def test_multi_step_lookup_then_calculate() -> None:
    chat = ScriptedChat(
        [
            _tool_assistant("c1", "lookup", {"key": "alpha"}, "查 alpha"),
            _tool_assistant("c2", "calculate", {"expression": "7*3"}, "再计算"),
            _final("结果是 21。"),
        ]
    )
    result = run_agent_loop("查 alpha 再乘以 3", chat, max_steps=5)
    assert result.stopped_reason == STOP_FINAL
    assert result.step_count == 3
    assert [s.kind for s in result.steps] == ["action", "action", "final"]
    obs1 = json.loads(result.steps[0].observations[0]["content"])
    obs2 = json.loads(result.steps[1].observations[0]["content"])
    assert obs1 == {"key": "alpha", "value": "7"}
    assert obs2["result"] == 21
    assert result.final_content == "结果是 21。"
    assert len(chat.calls) == 3


def test_max_steps_stop() -> None:
    chat = ScriptedChat(
        [
            _tool_assistant("a", "lookup", {"key": "alpha"}),
            _tool_assistant("b", "lookup", {"key": "beta"}),
            _tool_assistant("c", "lookup", {"key": "france_capital"}),
        ]
    )
    result = run_agent_loop("一直查", chat, max_steps=2)
    assert result.stopped_reason == STOP_MAX_STEPS
    assert result.step_count == 2
    assert all(s.kind == "action" for s in result.steps)
    assert result.final_content == "(stopped: max_steps)"
    assert len(chat.calls) == 2


def test_empty_goal_and_bad_chat_return() -> None:
    with pytest.raises(ValueError, match="goal"):
        run_agent_loop("   ", ScriptedChat([_final("x")]))

    chat = ScriptedChat([])  # won't be used if chat returns bad — inject manually

    def bad_chat(_messages: list) -> object:
        return "not-a-dict"

    with pytest.raises(ValueError, match="chat must return dict"):
        run_agent_loop("hello", bad_chat)  # type: ignore[arg-type]


def test_execute_must_return_list() -> None:
    chat = ScriptedChat(
        [_tool_assistant("c1", "lookup", {"key": "alpha"}), _final("ok")]
    )

    def bad_execute(_assistant: dict) -> object:
        return "nope"

    with pytest.raises(ValueError, match="execute must return list"):
        run_agent_loop("x", chat, execute=bad_execute)  # type: ignore[arg-type]


def test_render_trace_markdown() -> None:
    chat = ScriptedChat(
        [
            _tool_assistant("c1", "lookup", {"key": "beta"}, "查 beta"),
            _final("beta=3"),
        ]
    )
    result = run_agent_loop("查 beta", chat)
    text = render_trace_markdown(result)
    assert "查 beta" in text
    assert "Step 1" in text
    assert "Thought:" in text
    assert "Action:" in text
    assert "Observation:" in text
    assert "Stopped:" in text
    assert STOP_FINAL in text
    assert "Final:" in text


def test_default_execute_uses_tools() -> None:
    """不显式传 execute 时，默认走 tools.execute_assistant_tools。"""
    assistant = _tool_assistant("z", "calculate", {"expression": "2+2"})
    msgs = execute_assistant_tools(assistant)
    assert len(msgs) == 1
    assert json.loads(msgs[0]["content"])["result"] == 4
