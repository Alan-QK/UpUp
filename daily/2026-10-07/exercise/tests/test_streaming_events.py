"""Day 54 测试：流式事件 tool_start / tool_end 与工具状态派生。"""

from __future__ import annotations

import json

import pytest

from mini_framework import ERROR_PREFIX, STOP_FINAL, ScriptedChat
from streaming_events import (
    EVENT_FINAL,
    EVENT_RUN_END,
    EVENT_RUN_START,
    EVENT_THOUGHT,
    EVENT_TOOL_END,
    EVENT_TOOL_START,
    STATUS_ERROR,
    STATUS_OK,
    STATUS_RUNNING,
    AgentEvent,
    EventCollector,
    StreamingRunner,
    build_streaming_demo_agent,
    derive_tool_statuses,
    event_tool_end,
    event_tool_start,
    is_error_content,
    render_event_timeline,
)


def _call(call_id: str, name: str, arguments: dict | str) -> dict:
    if isinstance(arguments, dict):
        raw = json.dumps(arguments, ensure_ascii=False)
    else:
        raw = arguments
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": raw},
    }


def test_is_error_content() -> None:
    assert is_error_content(f"{ERROR_PREFIX} boom") is True
    assert is_error_content(f"  {ERROR_PREFIX} x") is True
    assert is_error_content("ok result") is False


def test_event_tool_start_and_end_helpers() -> None:
    start = event_tool_start(
        step=1,
        tool_name="lookup",
        call_id="c1",
        arguments={"key": "alpha"},
    )
    assert start.type == EVENT_TOOL_START
    assert start.tool_name == "lookup"
    assert start.call_id == "c1"
    assert start.arguments == {"key": "alpha"}

    ok_end = event_tool_end(
        step=1, tool_name="lookup", call_id="c1", content="7"
    )
    assert ok_end.type == EVENT_TOOL_END
    assert ok_end.status == STATUS_OK
    assert ok_end.content == "7"

    err_end = event_tool_end(
        step=1,
        tool_name="lookup",
        call_id="c1",
        content=f"{ERROR_PREFIX} KeyError: missing",
    )
    assert err_end.status == STATUS_ERROR


def test_event_collector_emit_and_callback() -> None:
    seen: list[str] = []
    collector = EventCollector(on_event=lambda e: seen.append(e.type))
    collector.emit(AgentEvent(type=EVENT_RUN_START, step=0, content="g"))
    collector.emit(
        event_tool_start(step=1, tool_name="lookup", call_id="c1", arguments={})
    )
    collector.emit(
        event_tool_end(step=1, tool_name="lookup", call_id="c1", content="7")
    )
    types = [e.type for e in collector.events()]
    assert types == [EVENT_RUN_START, EVENT_TOOL_START, EVENT_TOOL_END]
    assert seen == types


def test_event_collector_rejects_bad_tool_end() -> None:
    collector = EventCollector()
    with pytest.raises(ValueError):
        collector.emit(
            AgentEvent(
                type=EVENT_TOOL_END,
                step=1,
                tool_name="lookup",
                call_id="c1",
                status="weird",
            )
        )
    with pytest.raises(ValueError):
        collector.emit(
            AgentEvent(type=EVENT_TOOL_START, step=1, tool_name="", call_id="c1")
        )


def test_derive_tool_statuses_running_then_ok() -> None:
    events = [
        event_tool_start(
            step=1, tool_name="lookup", call_id="c1", arguments={"key": "alpha"}
        ),
        event_tool_end(step=1, tool_name="lookup", call_id="c1", content="7"),
        event_tool_start(
            step=2,
            tool_name="calculate",
            call_id="c2",
            arguments={"expression": "1+1"},
        ),
        event_tool_end(
            step=2,
            tool_name="calculate",
            call_id="c2",
            content=f"{ERROR_PREFIX} boom",
        ),
    ]
    statuses = derive_tool_statuses(events)
    assert len(statuses) == 2
    assert statuses[0]["call_id"] == "c1"
    assert statuses[0]["status"] == STATUS_OK
    assert statuses[0]["content"] == "7"
    assert statuses[0]["arguments"]["key"] == "alpha"
    assert statuses[1]["call_id"] == "c2"
    assert statuses[1]["status"] == STATUS_ERROR


def test_derive_partial_running() -> None:
    """只有 start 时，状态应为 running。"""
    events = [
        event_tool_start(step=1, tool_name="lookup", call_id="c9", arguments={}),
    ]
    statuses = derive_tool_statuses(events)
    assert statuses[0]["status"] == STATUS_RUNNING


def test_render_event_timeline() -> None:
    events = [
        AgentEvent(type=EVENT_RUN_START, step=0, content="goal"),
        event_tool_start(step=1, tool_name="lookup", call_id="c1", arguments={}),
        event_tool_end(step=1, tool_name="lookup", call_id="c1", content="7"),
        AgentEvent(type=EVENT_FINAL, step=2, content="done"),
    ]
    md = render_event_timeline(events)
    assert "# 事件时间线" in md
    assert "run_start" in md
    assert "tool_start" in md and "lookup" in md and "c1" in md
    assert "tool_end" in md and STATUS_OK in md
    assert "final" in md


def test_streaming_runner_emits_paired_tool_events() -> None:
    agent = build_streaming_demo_agent(max_steps=6)
    chat = ScriptedChat(
        [
            {
                "role": "assistant",
                "content": "查",
                "tool_calls": [_call("c1", "lookup", {"key": "alpha"})],
            },
            {
                "role": "assistant",
                "content": "算",
                "tool_calls": [_call("c2", "calculate", {"expression": "7*3"})],
            },
            {"role": "assistant", "content": "alpha=7，乘积 21。"},
        ]
    )
    live: list[str] = []
    bundled = StreamingRunner().run(
        agent, "查 alpha 再算 7*3", chat, on_event=lambda e: live.append(e.type)
    )
    result = bundled.result
    events = bundled.events

    assert result.stopped_reason == STOP_FINAL
    assert result.steps == 3
    assert result.tool_names_used == ("lookup", "calculate")
    assert "21" in result.final_content or "7" in result.final_content

    types = [e.type for e in events]
    assert types[0] == EVENT_RUN_START
    assert types[-1] == EVENT_RUN_END
    assert EVENT_THOUGHT in types
    assert EVENT_FINAL in types

    # 成对：两次 start / 两次 end
    assert types.count(EVENT_TOOL_START) == 2
    assert types.count(EVENT_TOOL_END) == 2

    # start 紧挨在对应 end 之前（同 call 的局部顺序）
    starts = [e for e in events if e.type == EVENT_TOOL_START]
    ends = [e for e in events if e.type == EVENT_TOOL_END]
    assert [e.call_id for e in starts] == ["c1", "c2"]
    assert [e.call_id for e in ends] == ["c1", "c2"]
    assert all(e.status == STATUS_OK for e in ends)

    statuses = derive_tool_statuses(events)
    assert [s["name"] for s in statuses] == ["lookup", "calculate"]
    assert all(s["status"] == STATUS_OK for s in statuses)

    # 回调收到的顺序与 collector 一致
    assert live == types


def test_streaming_runner_marks_tool_error() -> None:
    agent = build_streaming_demo_agent(max_steps=4)
    chat = ScriptedChat(
        [
            {
                "role": "assistant",
                "content": "查不存在的 key",
                "tool_calls": [_call("e1", "lookup", {"key": "nope"})],
            },
            {"role": "assistant", "content": "查无结果。"},
        ]
    )
    bundled = StreamingRunner().run(agent, "查 nope", chat)
    ends = [e for e in bundled.events if e.type == EVENT_TOOL_END]
    assert len(ends) == 1
    assert ends[0].status == STATUS_ERROR
    assert ends[0].content.startswith(ERROR_PREFIX)

    statuses = derive_tool_statuses(bundled.events)
    assert statuses[0]["status"] == STATUS_ERROR


def test_streaming_runner_rejects_empty_goal() -> None:
    agent = build_streaming_demo_agent()
    with pytest.raises(ValueError):
        StreamingRunner().run(agent, "   ", ScriptedChat([]))


def test_build_streaming_demo_agent() -> None:
    agent = build_streaming_demo_agent(max_steps=3)
    assert agent.name == "streaming-demo"
    assert agent.max_steps == 3
    assert agent.registry.names() == ("lookup", "calculate")
