"""Day 54 练习：流式事件与工具状态（tool_start / tool_end）。

目标：在 Agent Loop 执行工具前后发出产品化事件，并派生 UI 状态。
只用标准库。不要改 mini_framework.py / tools_builtin.py 的内核逻辑。
"""

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
        """校验并记录事件；若有回调则同步通知。

        TODO:
        1. event 必须是 AgentEvent
        2. event.type 必须在 VALID_EVENT_TYPES
        3. 若 type == tool_end：status 必须是 STATUS_OK 或 STATUS_ERROR
        4. 若 type 为 tool_start / tool_end：tool_name 与 call_id 都必须是非空 str
        5. append 深拷贝后的事件（arguments 用 copy.deepcopy）
        6. 若 self.on_event 非 None，调用它（传入同一条事件）
        """
        raise NotImplementedError("TODO: implement EventCollector.emit")

    def events(self) -> tuple[AgentEvent, ...]:
        """按发送顺序返回不可变事件元组。

        TODO: return tuple(self._events)
        """
        raise NotImplementedError("TODO: implement EventCollector.events")


def is_error_content(content: str) -> bool:
    """Observation 是否为错误（ERROR: 前缀）。

    TODO: content 转 str 后 lstrip，以 ERROR_PREFIX 开头 → True
    """
    raise NotImplementedError("TODO: implement is_error_content")


def event_tool_start(
    *,
    step: int,
    tool_name: str,
    call_id: str,
    arguments: dict[str, Any] | None = None,
) -> AgentEvent:
    """构造 tool_start 事件。

    TODO: type=EVENT_TOOL_START；arguments 默认 {}；深拷贝 arguments
    """
    raise NotImplementedError("TODO: implement event_tool_start")


def event_tool_end(
    *,
    step: int,
    tool_name: str,
    call_id: str,
    content: str,
) -> AgentEvent:
    """构造 tool_end 事件；根据 content 设置 status。

    TODO:
    - is_error_content(content) → STATUS_ERROR，否则 STATUS_OK
    - type=EVENT_TOOL_END；写入 content
    """
    raise NotImplementedError("TODO: implement event_tool_end")


def derive_tool_statuses(events: list[AgentEvent] | tuple[AgentEvent, ...]) -> list[dict[str, Any]]:
    """从事件流派生前端工具卡片状态（按首次出现顺序）。

    TODO:
    1. 遍历 events
    2. tool_start：用 call_id 建/更新条目 → status=running，记录 name / arguments
    3. tool_end：更新同 call_id → status=event.status，content=event.content
    4. 返回 list[dict]，每个 dict 至少含：
       call_id, name, status, content, arguments
    5. 忽略非 tool_* 事件；无 call_id 的 tool 事件可跳过
    """
    raise NotImplementedError("TODO: implement derive_tool_statuses")


def render_event_timeline(events: list[AgentEvent] | tuple[AgentEvent, ...]) -> str:
    """把事件流渲染成可读时间线 Markdown。

    TODO: 返回字符串，必须包含：
    - 标题行：`# 事件时间线`
    - 每个事件一行，格式大致：
      `- [step={step}] {type}`，tool 事件追加 ` · {tool_name} ({call_id})`
      tool_end 再追加 ` → {status}`
    - 末尾空行可有可无，但整体非空
    """
    raise NotImplementedError("TODO: implement render_event_timeline")


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
        """执行 Agent，并向 collector 推送流式事件。

        TODO 实现要点：
        1. 校验 agent / goal（空 goal → ValueError）；max_steps = validate_max_steps(...)
        2. collector = EventCollector(on_event=on_event)
        3. emit run_start（step=0, content=goal）
        4. 初始化 messages = [system, user]，与 AgentRunner 一致
        5. for step_index in 1..max_steps:
           a. assistant = chat(messages)；append 深拷贝
           b. thought = assistant_thought(...)；若非空 emit thought
           c. 若无 tool_calls：
              emit final；emit run_end(content=STOP_FINAL)；
              返回 StreamingRunResult(AgentRunResult(...), events)
           d. 对每条 tool_call（dict）：
              - 解析 call_id / name / arguments（坏参数 → arguments={}，执行仍走 registry）
              - emit tool_start
              - 用 registry.execute(name, arguments) 拿 content
                （若 name 空：content 用 ERROR: ... 字符串即可）
              - emit tool_end
              - append role=tool 消息（tool_call_id + content）
              - 记录 used tool names
        6. 若耗尽 max_steps：
           final_content="(stopped: max_steps)"；emit final；emit run_end(STOP_MAX_STEPS)
        7. AgentRunResult 字段与 Day52/53 一致（goal/messages/final_content/stopped_reason/steps/tool_names_used）

        提示：不必调用 AgentRunner().run；今天要自己在循环里插事件。
        ScriptedChat 可直接当 chat 用。
        """
        raise NotImplementedError("TODO: implement StreamingRunner.run")


def build_streaming_demo_agent(*, max_steps: int = 6) -> FrameworkAgent:
    """构建默认演示 Agent（内置 lookup/calculate）。

    TODO: return build_default_agent(name="streaming-demo", max_steps=max_steps)
    """
    raise NotImplementedError("TODO: implement build_streaming_demo_agent")


# 便于测试与 main 复用的小工具（已实现）
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
