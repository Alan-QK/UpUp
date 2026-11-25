"""Day 46 参考实现：手写最小 ReAct / Agent Loop。"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Callable

from tools import execute_assistant_tools, loop_toolkit

ChatFn = Callable[[list[dict[str, Any]]], dict[str, Any]]
ExecuteFn = Callable[[dict[str, Any]], list[dict[str, Any]]]

STOP_FINAL = "final_answer"
STOP_MAX_STEPS = "max_steps"
VALID_STOP_REASONS = (STOP_FINAL, STOP_MAX_STEPS)


@dataclass(frozen=True)
class LoopStep:
    """Loop 中的一步（一次模型调用 + 可选工具观察）。"""

    index: int
    kind: str  # "action" | "final"
    thought: str
    assistant: dict[str, Any]
    observations: list[dict[str, Any]]


@dataclass(frozen=True)
class LoopResult:
    """一次 Agent Loop 运行结果。"""

    goal: str
    messages: list[dict[str, Any]]
    steps: list[LoopStep]
    final_content: str
    stopped_reason: str
    step_count: int


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
        "你是 ReAct 风格助手，遵循 Thought → Action → Observation 循环。"
        f"可用工具：{names}。"
        "需要事实时先 lookup；需要精确运算时 calculate。"
        "信息足够后直接给出最终回答，不要再调用工具。"
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
    """抽取 Thought 文本（即 assistant.content）。"""
    if not isinstance(assistant_message, dict):
        return ""
    content = assistant_message.get("content")
    if content is None:
        return ""
    return normalize_text(str(content))


def validate_max_steps(max_steps: int) -> int:
    """校验 max_steps。"""
    if isinstance(max_steps, bool) or not isinstance(max_steps, int):
        raise ValueError("max_steps must be int")
    if max_steps < 1:
        raise ValueError("max_steps must be >= 1")
    return max_steps


def run_agent_loop(
    goal: str,
    chat: ChatFn,
    *,
    execute: ExecuteFn | None = None,
    system_prompt: str | None = None,
    max_steps: int = 6,
) -> LoopResult:
    """手写最小 Agent Loop。"""
    max_steps = validate_max_steps(max_steps)
    cleaned_goal = normalize_text(goal)
    if not cleaned_goal:
        raise ValueError("goal must be non-empty")

    execute_fn = execute or execute_assistant_tools
    system = system_prompt if system_prompt is not None else default_system_prompt()

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": cleaned_goal},
    ]
    steps: list[LoopStep] = []

    for index in range(1, max_steps + 1):
        assistant = chat(messages)
        if not isinstance(assistant, dict):
            raise ValueError("chat must return dict")

        assistant_copy = copy.deepcopy(assistant)
        messages.append(assistant_copy)
        thought = assistant_thought(assistant_copy)

        if not has_tool_calls(assistant_copy):
            step = LoopStep(
                index=index,
                kind="final",
                thought=thought,
                assistant=assistant_copy,
                observations=[],
            )
            steps.append(step)
            return LoopResult(
                goal=cleaned_goal,
                messages=messages,
                steps=steps,
                final_content=thought,
                stopped_reason=STOP_FINAL,
                step_count=len(steps),
            )

        tool_msgs = execute_fn(assistant_copy)
        if not isinstance(tool_msgs, list):
            raise ValueError("execute must return list")

        obs_copies = [copy.deepcopy(item) for item in tool_msgs]
        for item in obs_copies:
            messages.append(item)

        steps.append(
            LoopStep(
                index=index,
                kind="action",
                thought=thought,
                assistant=assistant_copy,
                observations=obs_copies,
            )
        )

    return LoopResult(
        goal=cleaned_goal,
        messages=messages,
        steps=steps,
        final_content="(stopped: max_steps)",
        stopped_reason=STOP_MAX_STEPS,
        step_count=len(steps),
    )


def render_trace_markdown(result: LoopResult) -> str:
    """把 LoopResult 渲染成便于阅读的 Markdown 轨迹。"""
    lines: list[str] = [
        f"# Agent Loop Trace · {result.goal}",
        "",
    ]
    for step in result.steps:
        lines.append(f"## Step {step.index} · {step.kind}")
        lines.append(f"- Thought: {step.thought or '(empty)'}")
        if step.kind == "action":
            names: list[str] = []
            for call in step.assistant.get("tool_calls") or []:
                if isinstance(call, dict):
                    fn = call.get("function") or {}
                    if isinstance(fn, dict):
                        names.append(str(fn.get("name", "?")))
            lines.append(f"- Action: {', '.join(names) if names else '(none)'}")
            for obs in step.observations:
                content = obs.get("content", "")
                lines.append(f"- Observation: {content}")
        lines.append("")

    lines.append(f"**Stopped:** {result.stopped_reason}")
    lines.append(f"**Final:** {result.final_content}")
    return "\n".join(lines)
