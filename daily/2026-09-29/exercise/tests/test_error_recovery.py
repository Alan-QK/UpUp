"""Day 48：工具错误恢复。"""

from __future__ import annotations

import json

import pytest

from error_recovery import (
    ERROR_PREFIX,
    STOP_FINAL,
    STOP_MAX_STEPS,
    STOP_TOO_MANY_ERRORS,
    RecoveryPolicy,
    ScriptedChat,
    assistant_thought,
    count_error_observations,
    has_tool_calls,
    is_error_content,
    normalize_text,
    observation_is_error,
    render_trace_markdown,
    run_recovery_loop,
    step_has_tool_error,
    validate_recovery_policy,
)
from tools import LOOKUP_KB, loop_toolkit


def _tool_assistant(
    call_id: str,
    name: str,
    arguments: dict | str,
    content: str | None = "思考中",
) -> dict:
    if isinstance(arguments, dict):
        args_text = json.dumps(arguments, ensure_ascii=False)
    else:
        args_text = arguments
    return {
        "role": "assistant",
        "content": content,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": args_text,
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


def test_error_detection() -> None:
    assert is_error_content(None) is False
    assert is_error_content("ok") is False
    assert is_error_content("ERROR: missing key") is True
    assert is_error_content("  ERROR: boom") is True
    assert is_error_content(f"{ERROR_PREFIX} x") is True

    assert observation_is_error(
        {"role": "tool", "tool_call_id": "1", "content": "ERROR: missing key"}
    )
    assert observation_is_error({"role": "tool", "content": '{"ok":1}'}) is False
    assert observation_is_error({"role": "assistant", "content": "ERROR: x"}) is False
    assert observation_is_error("bad") is False

    obs = [
        {"role": "tool", "content": "ERROR: a"},
        {"role": "tool", "content": '{"result":1}'},
        {"role": "tool", "content": "ERROR: b"},
    ]
    assert count_error_observations(obs) == 2
    assert step_has_tool_error(obs) is True
    assert step_has_tool_error([{"role": "tool", "content": '{"x":1}'}]) is False
    assert count_error_observations("bad") == 0  # type: ignore[arg-type]


def test_validate_recovery_policy() -> None:
    policy = RecoveryPolicy(max_steps=4, max_consecutive_errors=2)
    assert validate_recovery_policy(policy) is policy

    with pytest.raises(TypeError, match="RecoveryPolicy"):
        validate_recovery_policy({"max_steps": 3})  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_steps must be int"):
        validate_recovery_policy(RecoveryPolicy(max_steps=True))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_steps must be >= 1"):
        validate_recovery_policy(RecoveryPolicy(max_steps=0))

    with pytest.raises(ValueError, match="max_consecutive_errors must be int"):
        validate_recovery_policy(RecoveryPolicy(max_consecutive_errors=True))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_consecutive_errors must be >= 1"):
        validate_recovery_policy(RecoveryPolicy(max_consecutive_errors=0))


def test_direct_final_answer() -> None:
    chat = ScriptedChat([_final("不用工具也能答。")])
    result = run_recovery_loop("介绍错误恢复", chat, policy=RecoveryPolicy(max_steps=3))
    assert result.stopped_reason == STOP_FINAL
    assert result.step_count == 1
    assert result.recovery_count == 0
    assert result.consecutive_error_streak == 0
    assert result.final_content == "不用工具也能答。"


def test_recover_from_bad_calculate_args() -> None:
    """缺 expression → ERROR → 纠正后再算 → final。"""
    chat = ScriptedChat(
        [
            _tool_assistant("bad", "calculate", {}, "少了参数"),
            _tool_assistant(
                "ok", "calculate", {"expression": "7*3"}, "补上 expression"
            ),
            _final("结果是 21。"),
        ]
    )
    result = run_recovery_loop("算 7*3", chat)
    assert result.stopped_reason == STOP_FINAL
    assert [s.kind for s in result.steps] == ["error_action", "action", "final"]
    assert result.steps[0].error_count == 1
    assert result.steps[0].observations[0]["content"].startswith("ERROR:")
    assert result.steps[1].error_count == 0
    assert '"result":21' in result.steps[1].observations[0]["content"].replace(" ", "")
    assert result.recovery_count == 1
    assert result.final_content == "结果是 21。"
    # 第二轮 chat 入参应已包含 ERROR 观察，模型才能纠正
    assert any(
        isinstance(m, dict)
        and m.get("role") == "tool"
        and str(m.get("content", "")).startswith("ERROR:")
        for m in chat.calls[1]
    )


def test_recover_from_unknown_lookup_key() -> None:
    chat = ScriptedChat(
        [
            _tool_assistant("m1", "lookup", {"key": "gamma"}, "错键"),
            _tool_assistant("m2", "lookup", {"key": "alpha"}, "改成 alpha"),
            _final("alpha=7"),
        ]
    )
    result = run_recovery_loop("查 alpha", chat)
    assert result.stopped_reason == STOP_FINAL
    assert result.steps[0].kind == "error_action"
    assert "unknown key" in result.steps[0].observations[0]["content"]
    assert result.steps[1].kind == "action"
    assert result.recovery_count == 1


def test_recover_from_invalid_json_arguments() -> None:
    chat = ScriptedChat(
        [
            _tool_assistant("j1", "lookup", "{not-json", "坏 JSON"),
            _tool_assistant("j2", "lookup", {"key": "beta"}, "修好"),
            _final("beta=3"),
        ]
    )
    result = run_recovery_loop("查 beta", chat)
    assert result.stopped_reason == STOP_FINAL
    assert result.steps[0].kind == "error_action"
    assert "ERROR:" in result.steps[0].observations[0]["content"]
    assert result.recovery_count == 1


def test_error_then_final_counts_as_recovery() -> None:
    """ERROR 后模型直接作答（不再调工具）也算一次恢复。"""
    chat = ScriptedChat(
        [
            _tool_assistant("bad", "lookup", {"key": "nope"}),
            _final("查不到，我换个说法回答。"),
        ]
    )
    result = run_recovery_loop("容错收尾", chat)
    assert result.stopped_reason == STOP_FINAL
    assert [s.kind for s in result.steps] == ["error_action", "final"]
    assert result.recovery_count == 1


def test_too_many_consecutive_errors() -> None:
    chat = ScriptedChat(
        [
            _tool_assistant("a", "lookup", {"key": "nope1"}),
            _tool_assistant("b", "lookup", {"key": "nope2"}),
            _tool_assistant("c", "lookup", {"key": "nope3"}),
            _final("不该出现"),
        ]
    )
    policy = RecoveryPolicy(max_steps=6, max_consecutive_errors=3)
    result = run_recovery_loop("连续失败", chat, policy=policy)
    assert result.stopped_reason == STOP_TOO_MANY_ERRORS
    assert result.step_count == 3
    assert all(s.kind == "error_action" for s in result.steps)
    assert result.consecutive_error_streak == 3
    assert result.final_content == "(stopped: too_many_errors)"
    assert result.recovery_count == 0
    assert len(chat.calls) == 3


def test_error_streak_resets_after_success() -> None:
    """ERROR → 成功 → ERROR → 成功：不应触顶 consecutive=2。"""
    chat = ScriptedChat(
        [
            _tool_assistant("e1", "lookup", {"key": "nope"}),
            _tool_assistant("ok1", "lookup", {"key": "alpha"}),
            _tool_assistant("e2", "calculate", {}),
            _tool_assistant("ok2", "calculate", {"expression": "1+1"}),
            _final("好了"),
        ]
    )
    policy = RecoveryPolicy(max_steps=8, max_consecutive_errors=2)
    result = run_recovery_loop("交错恢复", chat, policy=policy)
    assert result.stopped_reason == STOP_FINAL
    assert [s.kind for s in result.steps] == [
        "error_action",
        "action",
        "error_action",
        "action",
        "final",
    ]
    assert result.recovery_count == 2


def test_max_steps_while_still_erroring() -> None:
    chat = ScriptedChat(
        [
            _tool_assistant("a", "lookup", {"key": "x"}),
            _tool_assistant("b", "lookup", {"key": "y"}),
        ]
    )
    policy = RecoveryPolicy(max_steps=2, max_consecutive_errors=5)
    result = run_recovery_loop("预算不够", chat, policy=policy)
    assert result.stopped_reason == STOP_MAX_STEPS
    assert result.step_count == 2
    assert result.consecutive_error_streak == 2
    assert result.final_content == "(stopped: max_steps)"


def test_empty_goal_and_bad_chat() -> None:
    with pytest.raises(ValueError, match="goal"):
        run_recovery_loop("  ", ScriptedChat([_final("x")]))

    def bad_chat(_messages: list) -> object:
        return "nope"

    with pytest.raises(ValueError, match="chat must return dict"):
        run_recovery_loop("hello", bad_chat)  # type: ignore[arg-type]


def test_render_trace_markdown() -> None:
    chat = ScriptedChat(
        [
            _tool_assistant("c1", "calculate", {}, "坏调用"),
            _tool_assistant("c2", "calculate", {"expression": "2+2"}, "纠正"),
            _final("等于 4"),
        ]
    )
    result = run_recovery_loop("算 2+2", chat)
    text = render_trace_markdown(result)
    assert "算 2+2" in text
    assert "Policy:" in text
    assert "recovery_count=" in text
    assert "Step 1" in text
    assert "error_action" in text
    assert "error_count:" in text
    assert "Stopped:" in text
    assert STOP_FINAL in text
    assert "Final:" in text
