"""Day 49 参考实现：轨迹日志 Trace。"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from tools import execute_assistant_tools, loop_toolkit

ChatFn = Callable[[list[dict[str, Any]]], dict[str, Any]]
ExecuteFn = Callable[[dict[str, Any]], list[dict[str, Any]]]
PrintFn = Callable[[str], None]

ERROR_PREFIX = "ERROR:"

STOP_FINAL = "final_answer"
STOP_MAX_STEPS = "max_steps"
VALID_STOP_REASONS = (STOP_FINAL, STOP_MAX_STEPS)


@dataclass(frozen=True)
class TracePolicy:
    """轨迹记录策略。"""

    max_steps: int = 6
    live_print: bool = True


@dataclass(frozen=True)
class ActionRecord:
    """一次工具调用的结构化记录。"""

    call_id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ObservationRecord:
    """一次工具观察的结构化记录。"""

    call_id: str
    content: str
    is_error: bool


@dataclass(frozen=True)
class TraceStep:
    """Loop 中的一步轨迹。"""

    index: int
    kind: str  # "action" | "final"
    thought: str
    actions: tuple[ActionRecord, ...]
    observations: tuple[ObservationRecord, ...]


@dataclass(frozen=True)
class TraceLog:
    """完整可回放轨迹。"""

    goal: str
    steps: tuple[TraceStep, ...]
    stopped_reason: str
    final_content: str
    max_steps: int


class ScriptedChat:
    """按顺序吐出预设 assistant 消息；记录每次入参 messages 的深拷贝。"""

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self._responses = [copy.deepcopy(item) for item in responses]
        self.calls: list[list[dict[str, Any]]] = []

    def __call__(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        self.calls.append(copy.deepcopy(messages))
        if not self._responses:
            raise RuntimeError("no more scripted responses")
        return copy.deepcopy(self._responses.pop(0))


def default_system_prompt() -> str:
    """返回 system 提示。"""
    names = "、".join(item["function"]["name"] for item in loop_toolkit())
    return (
        "你是带轨迹日志的 ReAct 助手。"
        f"可用工具：{names}。"
        "每一步都会被记录 Thought / Action / Observation。"
        "信息足够后直接给出最终回答。"
    )


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白压成单个空格。"""
    return " ".join(text.split())


def has_tool_calls(assistant_message: dict[str, Any]) -> bool:
    """是否包含至少一条 tool_call。"""
    if not isinstance(assistant_message, dict):
        return False
    raw = assistant_message.get("tool_calls")
    return isinstance(raw, list) and len(raw) > 0


def assistant_thought(assistant_message: dict[str, Any]) -> str:
    """抽取 Thought（assistant.content）。"""
    if not isinstance(assistant_message, dict):
        return ""
    content = assistant_message.get("content")
    if content is None:
        return ""
    return normalize_text(str(content))


def parse_arguments(raw: Any) -> dict[str, Any]:
    """解析 tool_call.function.arguments。"""
    if isinstance(raw, dict):
        return copy.deepcopy(raw)
    if raw is None:
        return {}
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("arguments must be valid JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("arguments JSON must be an object")
        return parsed
    raise ValueError("arguments must be str or dict")


def extract_actions(assistant_message: dict[str, Any]) -> tuple[ActionRecord, ...]:
    """从 assistant.tool_calls 提取 ActionRecord 元组。"""
    if not isinstance(assistant_message, dict):
        return ()
    raw_calls = assistant_message.get("tool_calls")
    if not isinstance(raw_calls, list):
        return ()

    records: list[ActionRecord] = []
    for call in raw_calls:
        if not isinstance(call, dict):
            continue
        call_id = str(call.get("id", "")).strip() or "unknown"
        fn = call.get("function")
        if isinstance(fn, dict):
            name = str(fn.get("name", "")).strip() or "unknown"
            args_raw = fn.get("arguments", "{}")
        else:
            name = "unknown"
            args_raw = "{}"
        try:
            arguments = parse_arguments(args_raw)
        except ValueError as exc:
            arguments = {"_raw": str(args_raw), "_error": str(exc)}
        records.append(ActionRecord(call_id=call_id, name=name, arguments=arguments))
    return tuple(records)


def extract_observations(
    tool_messages: list[dict[str, Any]],
) -> tuple[ObservationRecord, ...]:
    """从 role=tool 消息列表提取 ObservationRecord。"""
    if not isinstance(tool_messages, list):
        return ()

    records: list[ObservationRecord] = []
    for item in tool_messages:
        if not isinstance(item, dict):
            continue
        call_id = str(item.get("tool_call_id", "")).strip() or "unknown"
        raw_content = item.get("content")
        content = "" if raw_content is None else str(raw_content)
        is_error = content.lstrip().startswith(ERROR_PREFIX)
        records.append(
            ObservationRecord(call_id=call_id, content=content, is_error=is_error)
        )
    return tuple(records)


def format_action_line(action: ActionRecord) -> str:
    """格式化单条 Action 行。"""
    parts: list[str] = []
    for key in sorted(action.arguments):
        value = json.dumps(
            action.arguments[key], ensure_ascii=False, separators=(",", ":")
        )
        parts.append(f"{key}={value}")
    joined = ", ".join(parts)
    return f"Action: {action.name}({joined})"


def format_observation_line(observation: ObservationRecord) -> str:
    """格式化单条 Observation 行。"""
    if observation.is_error:
        return f"Observation ERROR: {observation.content.lstrip()}"
    return f"Observation: {observation.content}"


def format_step_block(step: TraceStep) -> str:
    """格式化一步的多行文本块（末尾无多余空行）。"""
    lines = [
        f"Step {step.index} · {step.kind}",
        f"  Thought: {step.thought or '(empty)'}",
    ]
    if step.kind == "final":
        return "\n".join(lines)

    if step.actions:
        for action in step.actions:
            lines.append(f"  {format_action_line(action)}")
    else:
        lines.append("  Action: (none)")

    if step.observations:
        for obs in step.observations:
            lines.append(f"  {format_observation_line(obs)}")
    else:
        lines.append("  Observation: (none)")

    return "\n".join(lines)


def render_trace_text(trace: TraceLog) -> str:
    """渲染完整可回放文本。"""
    lines: list[str] = [
        f"# Trace · {trace.goal}",
        "",
        f"- max_steps={trace.max_steps}",
        "",
    ]
    for step in trace.steps:
        lines.append(format_step_block(step))
        lines.append("")
    lines.append(f"**Stopped:** {trace.stopped_reason}")
    lines.append(f"**Final:** {trace.final_content}")
    return "\n".join(lines)


def action_to_dict(action: ActionRecord) -> dict[str, Any]:
    """ActionRecord → 可 JSON 序列化的 dict。"""
    return {
        "call_id": action.call_id,
        "name": action.name,
        "arguments": copy.deepcopy(action.arguments),
    }


def observation_to_dict(observation: ObservationRecord) -> dict[str, Any]:
    """ObservationRecord → dict。"""
    return {
        "call_id": observation.call_id,
        "content": observation.content,
        "is_error": observation.is_error,
    }


def step_to_dict(step: TraceStep) -> dict[str, Any]:
    """TraceStep → dict（含 type='step'）。"""
    return {
        "type": "step",
        "index": step.index,
        "kind": step.kind,
        "thought": step.thought,
        "actions": [action_to_dict(item) for item in step.actions],
        "observations": [observation_to_dict(item) for item in step.observations],
    }


def step_from_dict(data: dict[str, Any]) -> TraceStep:
    """dict → TraceStep。"""
    if not isinstance(data, dict):
        raise TypeError("step data must be dict")
    if "type" in data and data["type"] != "step":
        raise ValueError("expected type=step")

    actions_raw = data.get("actions") or []
    observations_raw = data.get("observations") or []
    actions = tuple(
        ActionRecord(
            call_id=str(item.get("call_id", "")),
            name=str(item.get("name", "")),
            arguments=copy.deepcopy(item.get("arguments") or {}),
        )
        for item in actions_raw
        if isinstance(item, dict)
    )
    observations = tuple(
        ObservationRecord(
            call_id=str(item.get("call_id", "")),
            content=str(item.get("content", "")),
            is_error=bool(item.get("is_error", False)),
        )
        for item in observations_raw
        if isinstance(item, dict)
    )
    return TraceStep(
        index=int(data.get("index", 0)),
        kind=str(data.get("kind", "")),
        thought=str(data.get("thought", "")),
        actions=actions,
        observations=observations,
    )


def validate_trace_policy(policy: TracePolicy) -> TracePolicy:
    """校验 TracePolicy。"""
    if not isinstance(policy, TracePolicy):
        raise TypeError("policy must be TracePolicy")

    if isinstance(policy.max_steps, bool) or not isinstance(policy.max_steps, int):
        raise ValueError("max_steps must be int")
    if policy.max_steps < 1:
        raise ValueError("max_steps must be >= 1")

    if not isinstance(policy.live_print, bool):
        raise ValueError("live_print must be bool")

    return policy


def dump_trace_jsonl(path: str | Path, trace: TraceLog) -> None:
    """把 TraceLog 写成 JSONL 文件。"""
    target = Path(path)
    lines = [
        json.dumps(
            {"type": "meta", "goal": trace.goal, "max_steps": trace.max_steps},
            ensure_ascii=False,
        ),
    ]
    for step in trace.steps:
        lines.append(json.dumps(step_to_dict(step), ensure_ascii=False))
    lines.append(
        json.dumps(
            {
                "type": "end",
                "stopped_reason": trace.stopped_reason,
                "final_content": trace.final_content,
            },
            ensure_ascii=False,
        )
    )
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_trace_jsonl(path: str | Path) -> TraceLog:
    """从 JSONL 加载 TraceLog。"""
    text = Path(path).read_text(encoding="utf-8")
    goal: str | None = None
    max_steps: int | None = None
    steps: list[TraceStep] = []
    stopped_reason: str | None = None
    final_content: str | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        data = json.loads(stripped)
        if not isinstance(data, dict):
            raise ValueError("jsonl line must be object")
        kind = data.get("type")
        if kind == "meta":
            goal = str(data.get("goal", ""))
            max_steps = int(data.get("max_steps", 0))
        elif kind == "step":
            steps.append(step_from_dict(data))
        elif kind == "end":
            stopped_reason = str(data.get("stopped_reason", ""))
            final_content = str(data.get("final_content", ""))
        else:
            raise ValueError(f"unknown jsonl type: {kind}")

    if goal is None or max_steps is None:
        raise ValueError("missing meta line")
    if stopped_reason is None or final_content is None:
        raise ValueError("missing end line")

    return TraceLog(
        goal=goal,
        steps=tuple(steps),
        stopped_reason=stopped_reason,
        final_content=final_content,
        max_steps=max_steps,
    )


def run_traced_loop(
    goal: str,
    chat: ChatFn,
    *,
    policy: TracePolicy | None = None,
    execute: ExecuteFn | None = None,
    system_prompt: str | None = None,
    printer: PrintFn | None = None,
) -> TraceLog:
    """带轨迹记录的 Agent Loop。"""
    resolved_policy = validate_trace_policy(policy or TracePolicy())
    cleaned_goal = normalize_text(goal)
    if not cleaned_goal:
        raise ValueError("goal must be non-empty")

    execute_fn = execute or execute_assistant_tools
    system = system_prompt if system_prompt is not None else default_system_prompt()
    emit: PrintFn = printer if printer is not None else print

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": cleaned_goal},
    ]
    steps: list[TraceStep] = []

    def _emit(step: TraceStep) -> None:
        if resolved_policy.live_print:
            emit(format_step_block(step))

    for index in range(1, resolved_policy.max_steps + 1):
        assistant = chat(messages)
        if not isinstance(assistant, dict):
            raise ValueError("chat must return dict")

        assistant_copy = copy.deepcopy(assistant)
        messages.append(assistant_copy)
        thought = assistant_thought(assistant_copy)

        if not has_tool_calls(assistant_copy):
            step = TraceStep(
                index=index,
                kind="final",
                thought=thought,
                actions=(),
                observations=(),
            )
            steps.append(step)
            _emit(step)
            return TraceLog(
                goal=cleaned_goal,
                steps=tuple(steps),
                stopped_reason=STOP_FINAL,
                final_content=thought,
                max_steps=resolved_policy.max_steps,
            )

        tool_msgs = execute_fn(assistant_copy)
        if not isinstance(tool_msgs, list):
            raise ValueError("execute must return list")

        obs_copies = [copy.deepcopy(item) for item in tool_msgs]
        for item in obs_copies:
            messages.append(item)

        actions = extract_actions(assistant_copy)
        observations = extract_observations(obs_copies)
        step = TraceStep(
            index=index,
            kind="action",
            thought=thought,
            actions=actions,
            observations=observations,
        )
        steps.append(step)
        _emit(step)

    return TraceLog(
        goal=cleaned_goal,
        steps=tuple(steps),
        stopped_reason=STOP_MAX_STEPS,
        final_content="(stopped: max_steps)",
        max_steps=resolved_policy.max_steps,
    )
