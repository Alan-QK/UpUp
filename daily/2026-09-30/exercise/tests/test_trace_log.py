"""Day 49：轨迹日志 Trace。"""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pytest

from tools import LOOKUP_KB, loop_toolkit
from trace_log import (
    STOP_FINAL,
    STOP_MAX_STEPS,
    ActionRecord,
    ObservationRecord,
    ScriptedChat,
    TraceLog,
    TracePolicy,
    TraceStep,
    assistant_thought,
    dump_trace_jsonl,
    extract_actions,
    extract_observations,
    format_action_line,
    format_observation_line,
    format_step_block,
    has_tool_calls,
    load_trace_jsonl,
    normalize_text,
    parse_arguments,
    render_trace_text,
    run_traced_loop,
    step_from_dict,
    step_to_dict,
    validate_trace_policy,
)


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


def test_parse_arguments() -> None:
    assert parse_arguments({"key": "alpha"}) == {"key": "alpha"}
    assert parse_arguments(None) == {}
    assert parse_arguments("   ") == {}
    assert parse_arguments('{"expression":"1+1"}') == {"expression": "1+1"}
    with pytest.raises(ValueError, match="valid JSON"):
        parse_arguments("{bad")
    with pytest.raises(ValueError, match="object"):
        parse_arguments("[1,2]")
    with pytest.raises(ValueError, match="str or dict"):
        parse_arguments(3)  # type: ignore[arg-type]


def test_extract_actions_and_observations() -> None:
    assistant = _tool_assistant("c1", "lookup", {"key": "alpha"}, "查一下")
    actions = extract_actions(assistant)
    assert len(actions) == 1
    assert actions[0].call_id == "c1"
    assert actions[0].name == "lookup"
    assert actions[0].arguments == {"key": "alpha"}

    bad = _tool_assistant("c2", "calculate", "{not-json", "坏参数")
    bad_actions = extract_actions(bad)
    assert bad_actions[0].name == "calculate"
    assert "_error" in bad_actions[0].arguments

    assert extract_actions("x") == ()  # type: ignore[arg-type]

    obs = extract_observations(
        [
            {"role": "tool", "tool_call_id": "c1", "content": '{"ok":1}'},
            {"role": "tool", "tool_call_id": "c2", "content": "  ERROR: missing"},
            "skip",  # type: ignore[list-item]
        ]
    )
    assert len(obs) == 2
    assert obs[0].is_error is False
    assert obs[1].is_error is True
    assert obs[1].content.startswith("  ERROR:")


def test_format_lines() -> None:
    action = ActionRecord(
        call_id="1",
        name="lookup",
        arguments={"key": "alpha", "extra": 1},
    )
    # keys 排序：extra 在前
    assert format_action_line(action) == 'Action: lookup(extra=1, key="alpha")'
    empty = ActionRecord(call_id="1", name="ping", arguments={})
    assert format_action_line(empty) == "Action: ping()"

    ok = ObservationRecord(call_id="1", content='{"v":1}', is_error=False)
    assert format_observation_line(ok) == 'Observation: {"v":1}'
    err = ObservationRecord(call_id="1", content="  ERROR: boom", is_error=True)
    assert format_observation_line(err) == "Observation ERROR: ERROR: boom"


def test_format_step_block_action_and_final() -> None:
    step = TraceStep(
        index=1,
        kind="action",
        thought="先查",
        actions=(ActionRecord("c1", "lookup", {"key": "alpha"}),),
        observations=(ObservationRecord("c1", '{"key":"alpha","value":"7"}', False),),
    )
    block = format_step_block(step)
    assert "Step 1 · action" in block
    assert "Thought: 先查" in block
    assert 'Action: lookup(key="alpha")' in block
    assert 'Observation: {"key":"alpha","value":"7"}' in block

    final = TraceStep(index=2, kind="final", thought="答完了", actions=(), observations=())
    final_block = format_step_block(final)
    assert "Step 2 · final" in final_block
    assert "Action:" not in final_block
    assert "Observation:" not in final_block

    empty_action = TraceStep(
        index=3, kind="action", thought="", actions=(), observations=()
    )
    empty_block = format_step_block(empty_action)
    assert "Thought: (empty)" in empty_block
    assert "Action: (none)" in empty_block
    assert "Observation: (none)" in empty_block


def test_validate_trace_policy() -> None:
    policy = TracePolicy(max_steps=4, live_print=False)
    assert validate_trace_policy(policy) is policy

    with pytest.raises(TypeError, match="TracePolicy"):
        validate_trace_policy({"max_steps": 3})  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_steps must be int"):
        validate_trace_policy(TracePolicy(max_steps=True))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="max_steps must be >= 1"):
        validate_trace_policy(TracePolicy(max_steps=0))

    with pytest.raises(ValueError, match="live_print must be bool"):
        validate_trace_policy(TracePolicy(live_print="yes"))  # type: ignore[arg-type]


def test_direct_final_with_live_print() -> None:
    buf = StringIO()
    chat = ScriptedChat([_final("不用工具。")])
    result = run_traced_loop(
        "直接答",
        chat,
        policy=TracePolicy(max_steps=3, live_print=True),
        printer=buf.write,
    )
    assert result.stopped_reason == STOP_FINAL
    assert result.final_content == "不用工具。"
    assert len(result.steps) == 1
    assert result.steps[0].kind == "final"
    assert "Step 1 · final" in buf.getvalue()
    assert "Thought: 不用工具。" in buf.getvalue()


def test_action_then_final_records_action_obs() -> None:
    buf = StringIO()
    chat = ScriptedChat(
        [
            _tool_assistant("c1", "lookup", {"key": "alpha"}, "查 alpha"),
            _final("alpha 的值是 7。"),
        ]
    )
    result = run_traced_loop(
        "查 alpha",
        chat,
        policy=TracePolicy(max_steps=4, live_print=True),
        printer=lambda s: buf.write(s + "\n"),
    )
    assert result.stopped_reason == STOP_FINAL
    assert [s.kind for s in result.steps] == ["action", "final"]
    assert result.steps[0].actions[0].name == "lookup"
    assert result.steps[0].observations[0].is_error is False
    assert '"value":"7"' in result.steps[0].observations[0].content.replace(" ", "")
    printed = buf.getvalue()
    assert 'Action: lookup(key="alpha")' in printed
    assert "Observation:" in printed
    assert "Step 2 · final" in printed


def test_live_print_off_silent() -> None:
    buf = StringIO()
    chat = ScriptedChat([_final("静音")])
    run_traced_loop(
        "静音模式",
        chat,
        policy=TracePolicy(max_steps=2, live_print=False),
        printer=buf.write,
    )
    assert buf.getvalue() == ""


def test_max_steps_stop() -> None:
    chat = ScriptedChat(
        [
            _tool_assistant("a", "lookup", {"key": "alpha"}),
            _tool_assistant("b", "lookup", {"key": "beta"}),
        ]
    )
    result = run_traced_loop(
        "一直查",
        chat,
        policy=TracePolicy(max_steps=2, live_print=False),
    )
    assert result.stopped_reason == STOP_MAX_STEPS
    assert result.final_content == "(stopped: max_steps)"
    assert len(result.steps) == 2


def test_jsonl_roundtrip(tmp_path: Path) -> None:
    chat = ScriptedChat(
        [
            _tool_assistant("c1", "calculate", {"expression": "7*3"}, "算一下"),
            _final("21"),
        ]
    )
    original = run_traced_loop(
        "算 7*3",
        chat,
        policy=TracePolicy(max_steps=5, live_print=False),
    )
    path = tmp_path / "trace.jsonl"
    dump_trace_jsonl(path, original)
    loaded = load_trace_jsonl(path)

    assert loaded.goal == original.goal
    assert loaded.max_steps == original.max_steps
    assert loaded.stopped_reason == original.stopped_reason
    assert loaded.final_content == original.final_content
    assert len(loaded.steps) == len(original.steps)
    assert loaded.steps[0].actions[0].name == "calculate"
    assert loaded.steps[0].actions[0].arguments == {"expression": "7*3"}

    text = render_trace_text(loaded)
    assert "# Trace · 算 7*3" in text
    assert 'Action: calculate(expression="7*3")' in text
    assert "**Stopped:** final_answer" in text
    assert "**Final:** 21" in text


def test_load_jsonl_errors(tmp_path: Path) -> None:
    missing_meta = tmp_path / "no-meta.jsonl"
    missing_meta.write_text(
        json.dumps({"type": "end", "stopped_reason": "x", "final_content": "y"}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="missing meta"):
        load_trace_jsonl(missing_meta)

    missing_end = tmp_path / "no-end.jsonl"
    missing_end.write_text(
        json.dumps({"type": "meta", "goal": "g", "max_steps": 1}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="missing end"):
        load_trace_jsonl(missing_end)

    bad_type = tmp_path / "bad-type.jsonl"
    bad_type.write_text(
        json.dumps({"type": "meta", "goal": "g", "max_steps": 1})
        + "\n"
        + json.dumps({"type": "weird"})
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown jsonl type"):
        load_trace_jsonl(bad_type)


def test_step_dict_roundtrip() -> None:
    step = TraceStep(
        index=1,
        kind="action",
        thought="t",
        actions=(ActionRecord("id", "lookup", {"key": "beta"}),),
        observations=(ObservationRecord("id", "ERROR: x", True),),
    )
    data = step_to_dict(step)
    assert data["type"] == "step"
    restored = step_from_dict(data)
    assert restored == step

    with pytest.raises(TypeError, match="dict"):
        step_from_dict("bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="type=step"):
        step_from_dict({"type": "meta", "index": 1})


def test_empty_goal_rejected() -> None:
    with pytest.raises(ValueError, match="goal must be non-empty"):
        run_traced_loop("   ", ScriptedChat([_final("x")]), policy=TracePolicy())


def test_render_trace_text_structure() -> None:
    trace = TraceLog(
        goal="demo",
        steps=(
            TraceStep(
                index=1,
                kind="action",
                thought="想",
                actions=(ActionRecord("1", "lookup", {"key": "beta"}),),
                observations=(
                    ObservationRecord("1", '{"key":"beta","value":"3"}', False),
                ),
            ),
            TraceStep(index=2, kind="final", thought="结束", actions=(), observations=()),
        ),
        stopped_reason=STOP_FINAL,
        final_content="结束",
        max_steps=6,
    )
    text = render_trace_text(trace)
    assert text.startswith("# Trace · demo\n")
    assert "- max_steps=6" in text
    assert "Step 1 · action" in text
    assert "Step 2 · final" in text
    assert text.strip().endswith("**Final:** 结束")
