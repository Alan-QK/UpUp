"""Day 47：终止条件与步数限制。"""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from stop_guard import (
    STOP_FINAL,
    STOP_LAST_STEP_TOOLS,
    STOP_MAX_STEPS,
    STOP_REPEATED,
    ScriptedChat,
    StopPolicy,
    assistant_thought,
    fingerprint_tool_calls,
    has_tool_calls,
    normalize_text,
    render_trace_markdown,
    run_guarded_loop,
    validate_stop_policy,
)
from tools import LOOKUP_KB, loop_toolkit


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


def test_toolkit_unchanged() -> None:
    names = [item["function"]["name"] for item in loop_toolkit()]
    assert names == ["lookup", "calculate"]
    assert "alpha" in LOOKUP_KB


def test_helpers() -> None:
    assert normalize_text("  a\n b\t c  ") == "a b c"
    assert has_tool_calls(_tool_assistant("c1", "lookup", {"key": "alpha"})) is True
    assert has_tool_calls(_final("hi")) is False
    assert has_tool_calls("bad") is False  # type: ignore[arg-type]
    assert assistant_thought(_final("  hello\nworld ")) == "hello world"
    assert assistant_thought({"role": "assistant", "content": None}) == ""


def test_validate_stop_policy() -> None:
    policy = StopPolicy(max_steps=4, max_identical_streak=3, block_tools_on_last_step=False)
    assert validate_stop_policy(policy) is policy

    with pytest.raises(TypeError, match="StopPolicy"):
        validate_stop_policy({"max_steps": 3})  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_steps must be int"):
        validate_stop_policy(StopPolicy(max_steps=True))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_steps must be >= 1"):
        validate_stop_policy(StopPolicy(max_steps=0))

    with pytest.raises(ValueError, match="max_identical_streak must be int"):
        validate_stop_policy(StopPolicy(max_identical_streak=True))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_identical_streak must be >= 1"):
        validate_stop_policy(StopPolicy(max_identical_streak=0))

    # dataclass 默认 True 合法；用 replace 塞入非 bool 测校验
    bad = replace(StopPolicy(), block_tools_on_last_step=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_tools_on_last_step must be bool"):
        validate_stop_policy(bad)


def test_fingerprint_stable_and_order_sensitive() -> None:
    a = _tool_assistant("1", "lookup", {"key": "alpha"})
    b = _tool_assistant("2", "lookup", {"key": "alpha"})
    # 不同 call id，相同 name+args → 指纹相同
    assert fingerprint_tool_calls(a) == fingerprint_tool_calls(b)
    assert fingerprint_tool_calls(a) == 'lookup:{"key":"alpha"}'

    # 参数键序不影响指纹（sort_keys）
    ordered = {
        "role": "assistant",
        "content": "x",
        "tool_calls": [
            {
                "id": "z",
                "type": "function",
                "function": {
                    "name": "calculate",
                    "arguments": '{"b":2,"a":1}',
                },
            }
        ],
    }
    reordered = {
        "role": "assistant",
        "content": "x",
        "tool_calls": [
            {
                "id": "z",
                "type": "function",
                "function": {
                    "name": "calculate",
                    "arguments": '{"a":1,"b":2}',
                },
            }
        ],
    }
    assert fingerprint_tool_calls(ordered) == fingerprint_tool_calls(reordered)
    assert fingerprint_tool_calls(_final("no tools")) == ""
    assert fingerprint_tool_calls("x") == ""  # type: ignore[arg-type]


def test_direct_final_answer() -> None:
    chat = ScriptedChat([_final("直接回答，不用工具。")])
    result = run_guarded_loop("介绍停止策略", chat, policy=StopPolicy(max_steps=3))
    assert result.stopped_reason == STOP_FINAL
    assert result.step_count == 1
    assert result.steps[0].kind == "final"
    assert result.final_content == "直接回答，不用工具。"
    assert result.policy.max_steps == 3


def test_happy_path_lookup_then_final() -> None:
    chat = ScriptedChat(
        [
            _tool_assistant("c1", "lookup", {"key": "france_capital"}, "先查"),
            _final("首都是 Paris。"),
        ]
    )
    result = run_guarded_loop("法国首都？", chat)
    assert result.stopped_reason == STOP_FINAL
    assert [s.kind for s in result.steps] == ["action", "final"]
    assert "Paris" in result.steps[0].observations[0]["content"]
    assert result.steps[0].action_fingerprint == 'lookup:{"key":"france_capital"}'


def test_repeated_action_stops_early() -> None:
    chat = ScriptedChat(
        [
            _tool_assistant("a", "lookup", {"key": "alpha"}, "再查"),
            _tool_assistant("b", "lookup", {"key": "alpha"}, "还是查"),
            _tool_assistant("c", "lookup", {"key": "alpha"}, "还查"),
            _final("不该走到这里"),
        ]
    )
    policy = StopPolicy(max_steps=6, max_identical_streak=2, block_tools_on_last_step=True)
    result = run_guarded_loop("卡死查询", chat, policy=policy)
    assert result.stopped_reason == STOP_REPEATED
    assert result.step_count == 2
    assert all(s.kind == "action" for s in result.steps)
    assert result.final_content == "(stopped: repeated_action)"
    assert len(chat.calls) == 2  # 熔断后不再问模型


def test_different_args_not_repeated() -> None:
    chat = ScriptedChat(
        [
            _tool_assistant("a", "lookup", {"key": "alpha"}),
            _tool_assistant("b", "lookup", {"key": "beta"}),
            _final("alpha=7, beta=3"),
        ]
    )
    result = run_guarded_loop(
        "查两个键",
        chat,
        policy=StopPolicy(max_identical_streak=2),
    )
    assert result.stopped_reason == STOP_FINAL
    assert result.step_count == 3


def test_block_tools_on_last_step() -> None:
    executed: list[dict] = []

    def tracking_execute(assistant: dict) -> list[dict]:
        executed.append(assistant)
        from tools import execute_assistant_tools

        return execute_assistant_tools(assistant)

    chat = ScriptedChat(
        [
            _tool_assistant("a", "lookup", {"key": "alpha"}),
            _tool_assistant("b", "lookup", {"key": "beta"}),
        ]
    )
    policy = StopPolicy(max_steps=2, max_identical_streak=5, block_tools_on_last_step=True)
    result = run_guarded_loop("预算紧张", chat, policy=policy, execute=tracking_execute)
    assert result.stopped_reason == STOP_LAST_STEP_TOOLS
    assert result.steps[-1].kind == "blocked"
    assert result.steps[-1].observations == []
    assert result.final_content == "(stopped: last_step_tools)"
    # 第 1 步执行了工具；第 2 步被拦截
    assert len(executed) == 1
    assert len(chat.calls) == 2


def test_max_steps_when_block_disabled() -> None:
    chat = ScriptedChat(
        [
            _tool_assistant("a", "lookup", {"key": "alpha"}),
            _tool_assistant("b", "lookup", {"key": "beta"}),
            _tool_assistant("c", "lookup", {"key": "france_capital"}),
        ]
    )
    policy = StopPolicy(
        max_steps=2,
        max_identical_streak=10,
        block_tools_on_last_step=False,
    )
    result = run_guarded_loop("跑满步数", chat, policy=policy)
    assert result.stopped_reason == STOP_MAX_STEPS
    assert result.step_count == 2
    assert all(s.kind == "action" for s in result.steps)
    assert result.final_content == "(stopped: max_steps)"
    assert len(result.steps[1].observations) == 1


def test_empty_goal_and_bad_chat() -> None:
    with pytest.raises(ValueError, match="goal"):
        run_guarded_loop("  ", ScriptedChat([_final("x")]))

    def bad_chat(_messages: list) -> object:
        return "nope"

    with pytest.raises(ValueError, match="chat must return dict"):
        run_guarded_loop("hello", bad_chat)  # type: ignore[arg-type]


def test_render_trace_markdown() -> None:
    chat = ScriptedChat(
        [
            _tool_assistant("c1", "lookup", {"key": "beta"}, "查 beta"),
            _final("beta=3"),
        ]
    )
    result = run_guarded_loop("查 beta", chat)
    text = render_trace_markdown(result)
    assert "查 beta" in text
    assert "Policy:" in text
    assert "Step 1" in text
    assert "Fingerprint:" in text
    assert "Stopped:" in text
    assert STOP_FINAL in text
    assert "Final:" in text
