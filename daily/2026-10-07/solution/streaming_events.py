"""Day 54 参考实现：流式事件与工具状态。"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Callable

from mini_framework import (
    ERROR_PREFIX,
    STOP_FINAL,
    STOP_MAX_STEPS,
    AgentRunResult,
    FrameworkAgent,
    ScriptedChat,
    assistant_thought,
    build_default_agent,
    has_tool_calls,
    parse_tool_arguments,
    validate_max_steps,
)
from tools_builtin import normalize_text

EventHandler = Callable[["AgentEvent"], None]

EVENT_RUN_START = "run_start"
EVENT_THOUGHT = "thought"
EVENT_TOOL_START = "tool_start"
EVENT_TOOL_END = "tool_end"
EVENT_FINAL = "final"
EVENT_RUN_END = "run_end"

VALID_EVENT_TYPES = (
    EVENT_RUN_START,
    EVENT_THOUGHT,
    EVENT_TOOL_START,
    EVENT_TOOL_END,
    EVENT_FINAL,
    EVENT_RUN_END,
)

STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_OK = "ok"
STATUS_ERROR = "error"

VALID_TOOL_STATUSES = (
    STATUS_PENDING,
    STATUS_RUNNING,
    STATUS_OK,
    STATUS_ERROR,
)


@dataclass(frozen=True)
class AgentEvent:
    """一次增量事件（可推给前端 / SSE）。"""

    type: str
    step: int = 0
    tool_name: str | None = None
    call_id: str | None = None
    status: str | None = None
    content: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StreamingRunResult:
    """带事件流的一次运行结果。"""

    result: AgentRunResult
    events: tuple[AgentEvent, ...]


@dataclass
class EventCollector:
    """收集事件；可选转发到 on_event 回调。"""

    on_event: EventHandler | None = None
    _events: list[AgentEvent] = field(default_factory=list)

    def emit(self, event: AgentEvent) -> None:
        if not isinstance(event, AgentEvent):
            raise TypeError("event must be AgentEvent")
        if event.type not in VALID_EVENT_TYPES:
            raise ValueError(f"invalid event type: {event.type}")
        if event.type == EVENT_TOOL_END:
            if event.status not in (STATUS_OK, STATUS_ERROR):
                raise ValueError("tool_end.status must be ok or error")
        if event.type in (EVENT_TOOL_START, EVENT_TOOL_END):
            if not isinstance(event.tool_name, str) or not event.tool_name.strip():
                raise ValueError("tool event requires non-empty tool_name")
            if not isinstance(event.call_id, str) or not event.call_id.strip():
                raise ValueError("tool event requires non-empty call_id")

        stored = AgentEvent(
            type=event.type,
            step=event.step,
            tool_name=event.tool_name,
            call_id=event.call_id,
            status=event.status,
            content=event.content,
            arguments=copy.deepcopy(event.arguments),
        )
        self._events.append(stored)
        if self.on_event is not None:
            self.on_event(stored)

    def events(self) -> tuple[AgentEvent, ...]:
        return tuple(self._events)


def is_error_content(content: str) -> bool:
    return str(content).lstrip().startswith(ERROR_PREFIX)


def event_tool_start(
    *,
    step: int,
    tool_name: str,
    call_id: str,
    arguments: dict[str, Any] | None = None,
) -> AgentEvent:
    return AgentEvent(
        type=EVENT_TOOL_START,
        step=step,
        tool_name=tool_name,
        call_id=call_id,
        arguments=copy.deepcopy(arguments or {}),
    )


def event_tool_end(
    *,
    step: int,
    tool_name: str,
    call_id: str,
    content: str,
) -> AgentEvent:
    status = STATUS_ERROR if is_error_content(content) else STATUS_OK
    return AgentEvent(
        type=EVENT_TOOL_END,
        step=step,
        tool_name=tool_name,
        call_id=call_id,
        status=status,
        content=str(content),
    )


def derive_tool_statuses(
    events: list[AgentEvent] | tuple[AgentEvent, ...],
) -> list[dict[str, Any]]:
    order: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    for event in events:
        if event.type == EVENT_TOOL_START:
            if not event.call_id:
                continue
            if event.call_id not in by_id:
                order.append(event.call_id)
            by_id[event.call_id] = {
                "call_id": event.call_id,
                "name": event.tool_name or "",
                "status": STATUS_RUNNING,
                "content": "",
                "arguments": copy.deepcopy(event.arguments),
            }
        elif event.type == EVENT_TOOL_END:
            if not event.call_id:
                continue
            if event.call_id not in by_id:
                order.append(event.call_id)
                by_id[event.call_id] = {
                    "call_id": event.call_id,
                    "name": event.tool_name or "",
                    "status": event.status or STATUS_OK,
                    "content": event.content,
                    "arguments": {},
                }
            else:
                row = by_id[event.call_id]
                row["status"] = event.status or STATUS_OK
                row["content"] = event.content
                if event.tool_name:
                    row["name"] = event.tool_name
    return [by_id[cid] for cid in order]


def render_event_timeline(
    events: list[AgentEvent] | tuple[AgentEvent, ...],
) -> str:
    lines = ["# 事件时间线", ""]
    for event in events:
        line = f"- [step={event.step}] {event.type}"
        if event.type in (EVENT_TOOL_START, EVENT_TOOL_END):
            line += f" · {event.tool_name} ({event.call_id})"
        if event.type == EVENT_TOOL_END and event.status:
            line += f" → {event.status}"
        lines.append(line)
    lines.append("")
    return "\n".join(lines)


class StreamingRunner:
    """带事件发射的 Runner（Loop 语义对齐 AgentRunner，但不改其源码）。"""

    def run(
        self,
        agent: FrameworkAgent,
        goal: str,
        chat: Callable[[list[dict[str, Any]]], dict[str, Any]],
        *,
        on_event: EventHandler | None = None,
    ) -> StreamingRunResult:
        if not isinstance(agent, FrameworkAgent):
            raise TypeError("agent must be FrameworkAgent")
        max_steps = validate_max_steps(agent.max_steps)
        cleaned_goal = normalize_text(goal)
        if not cleaned_goal:
            raise ValueError("goal must be non-empty")

        collector = EventCollector(on_event=on_event)
        collector.emit(
            AgentEvent(type=EVENT_RUN_START, step=0, content=cleaned_goal)
        )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": agent.system_prompt},
            {"role": "user", "content": cleaned_goal},
        ]
        used: list[str] = []

        for step_index in range(1, max_steps + 1):
            assistant = chat(messages)
            if not isinstance(assistant, dict):
                raise ValueError("chat must return dict")

            assistant_copy = copy.deepcopy(assistant)
            messages.append(assistant_copy)
            thought = assistant_thought(assistant_copy)
            if thought:
                collector.emit(
                    AgentEvent(
                        type=EVENT_THOUGHT,
                        step=step_index,
                        content=thought,
                    )
                )

            if not has_tool_calls(assistant_copy):
                collector.emit(
                    AgentEvent(
                        type=EVENT_FINAL,
                        step=step_index,
                        content=thought,
                    )
                )
                collector.emit(
                    AgentEvent(
                        type=EVENT_RUN_END,
                        step=step_index,
                        content=STOP_FINAL,
                    )
                )
                result = AgentRunResult(
                    goal=cleaned_goal,
                    messages=copy.deepcopy(messages),
                    final_content=thought,
                    stopped_reason=STOP_FINAL,
                    steps=step_index,
                    tool_names_used=tuple(used),
                )
                return StreamingRunResult(result=result, events=collector.events())

            raw_calls = assistant_copy.get("tool_calls") or []
            for call in raw_calls:
                if not isinstance(call, dict):
                    continue
                call_id = str(call.get("id") or "")
                fn = call.get("function") or {}
                if not isinstance(fn, dict):
                    tool_name = ""
                    arguments: dict[str, Any] = {}
                else:
                    tool_name = str(fn.get("name") or "")
                    try:
                        arguments = parse_tool_arguments(fn.get("arguments"))
                    except Exception:  # noqa: BLE001
                        arguments = {}

                if not call_id:
                    call_id = f"missing-{step_index}-{len(used)}"
                if not tool_name:
                    content = f"{ERROR_PREFIX} ValueError: missing tool name"
                    display_name = "(unknown)"
                else:
                    display_name = tool_name
                    used.append(tool_name)
                    content = agent.registry.execute(tool_name, arguments)

                collector.emit(
                    event_tool_start(
                        step=step_index,
                        tool_name=display_name,
                        call_id=call_id,
                        arguments=arguments,
                    )
                )
                collector.emit(
                    event_tool_end(
                        step=step_index,
                        tool_name=display_name,
                        call_id=call_id,
                        content=content,
                    )
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": content,
                    }
                )

        collector.emit(
            AgentEvent(
                type=EVENT_FINAL,
                step=max_steps,
                content="(stopped: max_steps)",
            )
        )
        collector.emit(
            AgentEvent(
                type=EVENT_RUN_END,
                step=max_steps,
                content=STOP_MAX_STEPS,
            )
        )
        result = AgentRunResult(
            goal=cleaned_goal,
            messages=copy.deepcopy(messages),
            final_content="(stopped: max_steps)",
            stopped_reason=STOP_MAX_STEPS,
            steps=max_steps,
            tool_names_used=tuple(used),
        )
        return StreamingRunResult(result=result, events=collector.events())


def build_streaming_demo_agent(*, max_steps: int = 6) -> FrameworkAgent:
    return build_default_agent(name="streaming-demo", max_steps=max_steps)


def _tool_call(call_id: str, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(arguments, ensure_ascii=False),
        },
    }


def demo_scripted_chat() -> ScriptedChat:
    """lookup alpha → calculate 7*3 → Final。"""
    return ScriptedChat(
        [
            {
                "role": "assistant",
                "content": "先查 alpha",
                "tool_calls": [_tool_call("c1", "lookup", {"key": "alpha"})],
            },
            {
                "role": "assistant",
                "content": "再算 7*3",
                "tool_calls": [
                    _tool_call("c2", "calculate", {"expression": "7*3"})
                ],
            },
            {
                "role": "assistant",
                "content": "alpha=7，7*3=21。",
            },
        ]
    )
