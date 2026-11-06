"""Day 48 参考实现：工具错误恢复。"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Callable

from tools import execute_assistant_tools, loop_toolkit

ChatFn = Callable[[list[dict[str, Any]]], dict[str, Any]]
ExecuteFn = Callable[[dict[str, Any]], list[dict[str, Any]]]

ERROR_PREFIX = "ERROR:"

STOP_FINAL = "final_answer"
STOP_MAX_STEPS = "max_steps"
STOP_TOO_MANY_ERRORS = "too_many_errors"
VALID_STOP_REASONS = (STOP_FINAL, STOP_MAX_STEPS, STOP_TOO_MANY_ERRORS)


@dataclass(frozen=True)
class RecoveryPolicy:
    """工具错误恢复策略。"""

    max_steps: int = 6
    max_consecutive_errors: int = 3


@dataclass(frozen=True)
class LoopStep:
    """Loop 中的一步。"""

    index: int
    kind: str  # "action" | "error_action" | "final"
    thought: str
    assistant: dict[str, Any]
    observations: list[dict[str, Any]]
    error_count: int


@dataclass(frozen=True)
class LoopResult:
    """一次恢复 Loop 运行结果。"""

    goal: str
    messages: list[dict[str, Any]]
    steps: list[LoopStep]
    final_content: str
    stopped_reason: str
    step_count: int
    recovery_count: int
    consecutive_error_streak: int
    policy: RecoveryPolicy


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
        "你是会自我纠正的 ReAct 助手。"
        f"可用工具：{names}。"
        "若工具返回以 ERROR: 开头的观察，请根据错误信息修正参数后重试；"
        "不要重复完全相同的错误调用。"
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


def is_error_content(content: Any) -> bool:
    """内容是否为 ERROR: 前缀的工具失败观察。"""
    if content is None:
        return False
    return str(content).lstrip().startswith(ERROR_PREFIX)


def observation_is_error(observation: Any) -> bool:
    """单条消息是否为失败的 tool 观察。"""
    if not isinstance(observation, dict):
        return False
    if observation.get("role") != "tool":
        return False
    return is_error_content(observation.get("content"))


def count_error_observations(observations: list[Any]) -> int:
    """统计观察列表中的 ERROR 条数。"""
    if not isinstance(observations, list):
        return 0
    return sum(1 for item in observations if observation_is_error(item))


def step_has_tool_error(observations: list[Any]) -> bool:
    """本步是否至少有一条 ERROR 观察。"""
    return count_error_observations(observations) > 0


def validate_recovery_policy(policy: RecoveryPolicy) -> RecoveryPolicy:
    """校验 RecoveryPolicy。"""
    if not isinstance(policy, RecoveryPolicy):
        raise TypeError("policy must be RecoveryPolicy")

    if isinstance(policy.max_steps, bool) or not isinstance(policy.max_steps, int):
        raise ValueError("max_steps must be int")
    if policy.max_steps < 1:
        raise ValueError("max_steps must be >= 1")

    if isinstance(policy.max_consecutive_errors, bool) or not isinstance(
        policy.max_consecutive_errors, int
    ):
        raise ValueError("max_consecutive_errors must be int")
    if policy.max_consecutive_errors < 1:
        raise ValueError("max_consecutive_errors must be >= 1")

    return policy


def run_recovery_loop(
    goal: str,
    chat: ChatFn,
    *,
    policy: RecoveryPolicy | None = None,
    execute: ExecuteFn | None = None,
    system_prompt: str | None = None,
) -> LoopResult:
    """带工具错误恢复的 Agent Loop。

    核心差异（相对「遇错即崩」）：
    - 工具失败以 ERROR: 观察回填，Loop 继续
    - 模型可在下一步用正确参数重试（recovery）
    - 连续「含 ERROR 的 action 步」达到上限 → too_many_errors
    """
    resolved_policy = validate_recovery_policy(policy or RecoveryPolicy())
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
    consecutive_errors = 0
    recovery_count = 0

    for index in range(1, resolved_policy.max_steps + 1):
        assistant = chat(messages)
        if not isinstance(assistant, dict):
            raise ValueError("chat must return dict")

        assistant_copy = copy.deepcopy(assistant)
        messages.append(assistant_copy)
        thought = assistant_thought(assistant_copy)

        if not has_tool_calls(assistant_copy):
            # 仍处在错误 streak 时直接收尾，也算一次恢复闭环
            if consecutive_errors > 0:
                recovery_count += 1
            steps.append(
                LoopStep(
                    index=index,
                    kind="final",
                    thought=thought,
                    assistant=assistant_copy,
                    observations=[],
                    error_count=0,
                )
            )
            return LoopResult(
                goal=cleaned_goal,
                messages=messages,
                steps=steps,
                final_content=thought,
                stopped_reason=STOP_FINAL,
                step_count=len(steps),
                recovery_count=recovery_count,
                consecutive_error_streak=0,
                policy=resolved_policy,
            )

        tool_msgs = execute_fn(assistant_copy)
        if not isinstance(tool_msgs, list):
            raise ValueError("execute must return list")

        obs_copies = [copy.deepcopy(item) for item in tool_msgs]
        for item in obs_copies:
            messages.append(item)

        err_count = count_error_observations(obs_copies)
        has_error = err_count > 0

        if has_error:
            consecutive_errors += 1
            kind = "error_action"
        else:
            # 错误 streak → 成功工具步：计一次 recovery
            if consecutive_errors > 0:
                recovery_count += 1
            consecutive_errors = 0
            kind = "action"

        steps.append(
            LoopStep(
                index=index,
                kind=kind,
                thought=thought,
                assistant=assistant_copy,
                observations=obs_copies,
                error_count=err_count,
            )
        )

        if consecutive_errors >= resolved_policy.max_consecutive_errors:
            return LoopResult(
                goal=cleaned_goal,
                messages=messages,
                steps=steps,
                final_content="(stopped: too_many_errors)",
                stopped_reason=STOP_TOO_MANY_ERRORS,
                step_count=len(steps),
                recovery_count=recovery_count,
                consecutive_error_streak=consecutive_errors,
                policy=resolved_policy,
            )

    return LoopResult(
        goal=cleaned_goal,
        messages=messages,
        steps=steps,
        final_content="(stopped: max_steps)",
        stopped_reason=STOP_MAX_STEPS,
        step_count=len(steps),
        recovery_count=recovery_count,
        consecutive_error_streak=consecutive_errors,
        policy=resolved_policy,
    )


def render_trace_markdown(result: LoopResult) -> str:
    """渲染 Markdown 轨迹。"""
    policy = result.policy
    lines: list[str] = [
        f"# Recovery Loop Trace · {result.goal}",
        "",
        (
            f"- Policy: max_steps={policy.max_steps}, "
            f"max_consecutive_errors={policy.max_consecutive_errors}"
        ),
        f"- recovery_count={result.recovery_count}",
        "",
    ]
    for step in result.steps:
        lines.append(f"## Step {step.index} · {step.kind}")
        lines.append(f"- Thought: {step.thought or '(empty)'}")
        if step.kind != "final":
            names: list[str] = []
            for call in step.assistant.get("tool_calls") or []:
                if isinstance(call, dict):
                    fn = call.get("function") or {}
                    if isinstance(fn, dict):
                        names.append(str(fn.get("name", "?")))
            lines.append(f"- Action: {', '.join(names) if names else '(none)'}")
            lines.append(f"- error_count: {step.error_count}")
            for obs in step.observations:
                lines.append(f"- Observation: {obs.get('content', '')}")
        lines.append("")

    lines.append(f"**Stopped:** {result.stopped_reason}")
    lines.append(f"**Final:** {result.final_content}")
    return "\n".join(lines)
