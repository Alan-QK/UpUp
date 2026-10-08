"""Day 47 参考实现：终止条件与步数限制。"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from typing import Any, Callable

from tools import execute_assistant_tools, loop_toolkit, parse_tool_call

ChatFn = Callable[[list[dict[str, Any]]], dict[str, Any]]
ExecuteFn = Callable[[dict[str, Any]], list[dict[str, Any]]]

STOP_FINAL = "final_answer"
STOP_MAX_STEPS = "max_steps"
STOP_REPEATED = "repeated_action"
STOP_LAST_STEP_TOOLS = "last_step_tools"
VALID_STOP_REASONS = (
    STOP_FINAL,
    STOP_MAX_STEPS,
    STOP_REPEATED,
    STOP_LAST_STEP_TOOLS,
)


@dataclass(frozen=True)
class StopPolicy:
    """Agent Loop 停止策略。"""

    max_steps: int = 6
    max_identical_streak: int = 2
    block_tools_on_last_step: bool = True


@dataclass(frozen=True)
class LoopStep:
    """Loop 中的一步。"""

    index: int
    kind: str  # "action" | "final" | "blocked"
    thought: str
    assistant: dict[str, Any]
    observations: list[dict[str, Any]]
    action_fingerprint: str


@dataclass(frozen=True)
class LoopResult:
    """一次守卫 Loop 运行结果。"""

    goal: str
    messages: list[dict[str, Any]]
    steps: list[LoopStep]
    final_content: str
    stopped_reason: str
    step_count: int
    policy: StopPolicy


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
        "你是带停止策略的 ReAct 助手。"
        f"可用工具：{names}。"
        "需要事实时 lookup；需要运算时 calculate。"
        "信息足够后直接给出最终回答；不要重复同一个工具调用。"
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


def validate_stop_policy(policy: StopPolicy) -> StopPolicy:
    """校验 StopPolicy。"""
    if not isinstance(policy, StopPolicy):
        raise TypeError("policy must be StopPolicy")

    if isinstance(policy.max_steps, bool) or not isinstance(policy.max_steps, int):
        raise ValueError("max_steps must be int")
    if policy.max_steps < 1:
        raise ValueError("max_steps must be >= 1")

    if isinstance(policy.max_identical_streak, bool) or not isinstance(
        policy.max_identical_streak, int
    ):
        raise ValueError("max_identical_streak must be int")
    if policy.max_identical_streak < 1:
        raise ValueError("max_identical_streak must be >= 1")

    if not isinstance(policy.block_tools_on_last_step, bool):
        raise ValueError("block_tools_on_last_step must be bool")

    return policy


def fingerprint_tool_calls(assistant_message: dict[str, Any]) -> str:
    """为 assistant 的 tool_calls 生成稳定指纹。"""
    if not isinstance(assistant_message, dict):
        return ""
    raw_calls = assistant_message.get("tool_calls")
    if not isinstance(raw_calls, list) or not raw_calls:
        return ""

    parts: list[str] = []
    for item in raw_calls:
        try:
            _call_id, name, args = parse_tool_call(item)
            args_json = json.dumps(
                args, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            parts.append(f"{name}:{args_json}")
        except ValueError:
            parts.append("invalid")
    return "|".join(parts)


def run_guarded_loop(
    goal: str,
    chat: ChatFn,
    *,
    policy: StopPolicy | None = None,
    execute: ExecuteFn | None = None,
    system_prompt: str | None = None,
) -> LoopResult:
    """带停止策略的 Agent Loop。"""
    resolved_policy = validate_stop_policy(policy or StopPolicy())
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
    streak = 0
    last_fp: str | None = None

    for index in range(1, resolved_policy.max_steps + 1):
        assistant = chat(messages)
        if not isinstance(assistant, dict):
            raise ValueError("chat must return dict")

        assistant_copy = copy.deepcopy(assistant)
        messages.append(assistant_copy)
        thought = assistant_thought(assistant_copy)

        if not has_tool_calls(assistant_copy):
            steps.append(
                LoopStep(
                    index=index,
                    kind="final",
                    thought=thought,
                    assistant=assistant_copy,
                    observations=[],
                    action_fingerprint="",
                )
            )
            return LoopResult(
                goal=cleaned_goal,
                messages=messages,
                steps=steps,
                final_content=thought,
                stopped_reason=STOP_FINAL,
                step_count=len(steps),
                policy=resolved_policy,
            )

        fp = fingerprint_tool_calls(assistant_copy)

        if index == resolved_policy.max_steps and resolved_policy.block_tools_on_last_step:
            steps.append(
                LoopStep(
                    index=index,
                    kind="blocked",
                    thought=thought,
                    assistant=assistant_copy,
                    observations=[],
                    action_fingerprint=fp,
                )
            )
            return LoopResult(
                goal=cleaned_goal,
                messages=messages,
                steps=steps,
                final_content="(stopped: last_step_tools)",
                stopped_reason=STOP_LAST_STEP_TOOLS,
                step_count=len(steps),
                policy=resolved_policy,
            )

        tool_msgs = execute_fn(assistant_copy)
        if not isinstance(tool_msgs, list):
            raise ValueError("execute must return list")

        obs_copies = [copy.deepcopy(item) for item in tool_msgs]
        for item in obs_copies:
            messages.append(item)

        if fp == last_fp:
            streak += 1
        else:
            streak = 1
        last_fp = fp

        steps.append(
            LoopStep(
                index=index,
                kind="action",
                thought=thought,
                assistant=assistant_copy,
                observations=obs_copies,
                action_fingerprint=fp,
            )
        )

        if streak >= resolved_policy.max_identical_streak:
            return LoopResult(
                goal=cleaned_goal,
                messages=messages,
                steps=steps,
                final_content="(stopped: repeated_action)",
                stopped_reason=STOP_REPEATED,
                step_count=len(steps),
                policy=resolved_policy,
            )

    return LoopResult(
        goal=cleaned_goal,
        messages=messages,
        steps=steps,
        final_content="(stopped: max_steps)",
        stopped_reason=STOP_MAX_STEPS,
        step_count=len(steps),
        policy=resolved_policy,
    )


def render_trace_markdown(result: LoopResult) -> str:
    """渲染 Markdown 轨迹。"""
    policy = result.policy
    lines: list[str] = [
        f"# Guarded Loop Trace · {result.goal}",
        "",
        (
            f"- Policy: max_steps={policy.max_steps}, "
            f"streak={policy.max_identical_streak}, "
            f"block_last={policy.block_tools_on_last_step}"
        ),
        "",
    ]
    for step in result.steps:
        lines.append(f"## Step {step.index} · {step.kind}")
        lines.append(f"- Thought: {step.thought or '(empty)'}")
        if step.kind != "final":
            lines.append(f"- Fingerprint: {step.action_fingerprint or '(none)'}")
            names: list[str] = []
            for call in step.assistant.get("tool_calls") or []:
                if isinstance(call, dict):
                    fn = call.get("function") or {}
                    if isinstance(fn, dict):
                        names.append(str(fn.get("name", "?")))
            lines.append(f"- Action: {', '.join(names) if names else '(none)'}")
            if step.kind == "action":
                for obs in step.observations:
                    lines.append(f"- Observation: {obs.get('content', '')}")
            elif step.kind == "blocked":
                lines.append("- Observation: (blocked, not executed)")
        lines.append("")

    lines.append(f"**Stopped:** {result.stopped_reason}")
    lines.append(f"**Final:** {result.final_content}")
    return "\n".join(lines)
