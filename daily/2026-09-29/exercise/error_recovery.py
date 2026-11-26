"""Day 48 练习：工具错误恢复（非法参数时让模型纠正）。

请完成 TODO，使 tests/ 全部通过。
tools.py 已给齐，可直接 import。
全程只用标准库。
"""

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
    """返回 system 提示（已实现，可直接用）。"""
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
    # TODO: 实现
    raise NotImplementedError


def has_tool_calls(assistant_message: dict[str, Any]) -> bool:
    """是否包含至少一条 tool_call。

    规则：
    - 非 dict → False
    - tool_calls 为非空 list → True
    - 否则 False
    """
    # TODO: 实现
    raise NotImplementedError


def assistant_thought(assistant_message: dict[str, Any]) -> str:
    """抽取 Thought（assistant.content）。

    规则：
    - 非 dict → ""
    - content 为 None → ""
    - 否则 normalize_text(str(content))
    """
    # TODO: 实现
    raise NotImplementedError


def is_error_content(content: Any) -> bool:
    """内容是否为 ERROR: 前缀的工具失败观察。

    规则：
    - content 为 None → False
    - 转为 str 后先 lstrip，再判断是否以 ERROR_PREFIX 开头
    """
    # TODO: 实现
    raise NotImplementedError


def observation_is_error(observation: Any) -> bool:
    """单条消息是否为失败的 tool 观察。

    规则：
    - 非 dict → False
    - role 必须是 "tool"
    - content 满足 is_error_content
    """
    # TODO: 实现
    raise NotImplementedError


def count_error_observations(observations: list[Any]) -> int:
    """统计观察列表中的 ERROR 条数。

    规则：
    - observations 非 list → 0
    - 否则对每条调用 observation_is_error 计数
    """
    # TODO: 实现
    raise NotImplementedError


def step_has_tool_error(observations: list[Any]) -> bool:
    """本步是否至少有一条 ERROR 观察。"""
    # TODO: 实现（可用 count_error_observations）
    raise NotImplementedError


def validate_recovery_policy(policy: RecoveryPolicy) -> RecoveryPolicy:
    """校验 RecoveryPolicy。

    规则：
    - policy 必须是 RecoveryPolicy，否则 TypeError("policy must be RecoveryPolicy")
    - max_steps：必须是 int（bool 不算），否则 ValueError("max_steps must be int")
      且 >= 1，否则 ValueError("max_steps must be >= 1")
    - max_consecutive_errors：必须是 int（bool 不算），否则
      ValueError("max_consecutive_errors must be int")；且 >= 1，否则
      ValueError("max_consecutive_errors must be >= 1")
    - 返回原 policy
    """
    # TODO: 实现
    raise NotImplementedError


def run_recovery_loop(
    goal: str,
    chat: ChatFn,
    *,
    policy: RecoveryPolicy | None = None,
    execute: ExecuteFn | None = None,
    system_prompt: str | None = None,
) -> LoopResult:
    """带工具错误恢复的 Agent Loop。

    流程：
    1. policy 默认 RecoveryPolicy()；先 validate_recovery_policy
    2. goal 经 normalize_text 后不得为空，否则 ValueError("goal must be non-empty")
    3. execute 默认 execute_assistant_tools；system 默认 default_system_prompt()
    4. messages = [system, user(goal)]
    5. consecutive_errors=0；recovery_count=0
    6. for index in 1..policy.max_steps:
         - assistant = chat(messages)；必须是 dict，否则 ValueError("chat must return dict")
         - 深拷贝 append；thought = assistant_thought(...)
         - 若无 tool_calls：
             若 consecutive_errors > 0：recovery_count += 1（错误 streak 直接收尾）
             记 kind="final"，error_count=0
             stopped_reason=final_answer，consecutive_error_streak=0，返回
         - tool_msgs = execute(...)；必须是 list，否则 ValueError("execute must return list")
           深拷贝 append 每条观察
         - err_count = count_error_observations(...)
         - 若 err_count > 0：
             consecutive_errors += 1；kind="error_action"
           否则：
             若 consecutive_errors > 0：recovery_count += 1（错误→成功工具）
             consecutive_errors = 0；kind="action"
         - 记 LoopStep（含 error_count）
         - 若 consecutive_errors >= max_consecutive_errors：
             stopped_reason=too_many_errors
             final_content="(stopped: too_many_errors)"
             consecutive_error_streak=consecutive_errors，返回
    7. 循环自然结束：
       stopped_reason=max_steps，final_content="(stopped: max_steps)"
       consecutive_error_streak=当前 consecutive_errors

    注意：
    - step_count == len(steps)
    - LoopResult.policy 为校验后的同一 policy 对象
    - 「恢复」只在错误 streak 结束时计一次：成功工具步清零，或仍处 streak 时直接 final
    """
    # TODO: 实现
    raise NotImplementedError


def render_trace_markdown(result: LoopResult) -> str:
    """渲染 Markdown 轨迹。

    要求包含：
    - 标题含 goal
    - Policy 行：max_steps / max_consecutive_errors
    - recovery_count 行
    - 每步 Step N · kind；Thought；若非 final 则 Action / error_count / Observation
    - 结尾 Stopped + Final
    """
    # TODO: 实现
    raise NotImplementedError
