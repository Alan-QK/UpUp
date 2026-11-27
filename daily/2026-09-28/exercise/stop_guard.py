"""Day 47 练习：终止条件与步数限制（StopPolicy + 守卫 Loop）。

请完成 TODO，使 tests/ 全部通过。
tools.py 已给齐，可直接 import。
全程只用标准库。
"""

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
    """返回 system 提示（已实现，可直接用）。"""
    names = "、".join(item["function"]["name"] for item in loop_toolkit())
    return (
        "你是带停止策略的 ReAct 助手。"
        f"可用工具：{names}。"
        "需要事实时 lookup；需要运算时 calculate。"
        "信息足够后直接给出最终回答；不要重复同一个工具调用。"
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


def validate_stop_policy(policy: StopPolicy) -> StopPolicy:
    """校验 StopPolicy。

    规则：
    - policy 必须是 StopPolicy，否则 TypeError("policy must be StopPolicy")
    - max_steps：必须是 int（bool 不算），否则 ValueError("max_steps must be int")
      且 >= 1，否则 ValueError("max_steps must be >= 1")
    - max_identical_streak：必须是 int（bool 不算），否则
      ValueError("max_identical_streak must be int")；且 >= 1，否则
      ValueError("max_identical_streak must be >= 1")
    - block_tools_on_last_step：必须是 bool，否则
      ValueError("block_tools_on_last_step must be bool")
    - 返回原 policy
    """
    # TODO: 实现
    raise NotImplementedError


def fingerprint_tool_calls(assistant_message: dict[str, Any]) -> str:
    """为 assistant 的 tool_calls 生成稳定指纹。

    规则：
    1. 若无 tool_calls（或非 dict）→ 返回 ""
    2. 对每条 call：用 tools.parse_tool_call 得到 (id, name, args)
       - 若某条解析失败：该条指纹记为 "invalid"
    3. 单条指纹格式：f"{name}:{json.dumps(args, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"
       （invalid 条就用字面量 "invalid"）
    4. 多条按顺序用 "|" 拼接
    """
    # TODO: 实现
    raise NotImplementedError


def run_guarded_loop(
    goal: str,
    chat: ChatFn,
    *,
    policy: StopPolicy | None = None,
    execute: ExecuteFn | None = None,
    system_prompt: str | None = None,
) -> LoopResult:
    """带停止策略的 Agent Loop。

    流程：
    1. policy 默认 StopPolicy()；先 validate_stop_policy
    2. goal 经 normalize_text 后不得为空，否则 ValueError("goal must be non-empty")
    3. execute 默认 execute_assistant_tools；system 默认 default_system_prompt()
    4. messages = [system, user(goal)]
    5. streak=0；last_fp=None
    6. for index in 1..policy.max_steps:
         - assistant = chat(messages)；必须是 dict，否则 ValueError("chat must return dict")
         - 深拷贝 append；thought = assistant_thought(...)
         - 若无 tool_calls：
             记 kind="final"，fingerprint=""，stopped_reason=final_answer，
             final_content=thought，返回
         - fp = fingerprint_tool_calls(assistant_copy)
         - 若 index == max_steps 且 block_tools_on_last_step：
             记 kind="blocked"，observations=[]，action_fingerprint=fp
             stopped_reason=last_step_tools
             final_content="(stopped: last_step_tools)"，返回（**不**调用 execute）
         - tool_msgs = execute(...)；必须是 list，否则 ValueError("execute must return list")
           深拷贝 append 每条观察
         - 更新 streak：若 fp == last_fp 则 streak+1，否则 streak=1；然后 last_fp=fp
         - 记 kind="action"
         - 若 streak >= max_identical_streak：
             stopped_reason=repeated_action
             final_content="(stopped: repeated_action)"，返回
    7. 若循环自然结束（仅当 block_tools_on_last_step=False 且最后一步执行了工具）：
       stopped_reason=max_steps，final_content="(stopped: max_steps)"

    注意：
    - step_count == len(steps)
    - LoopResult.policy 为校验后的同一 policy 对象
    """
    # TODO: 实现
    raise NotImplementedError


def render_trace_markdown(result: LoopResult) -> str:
    """渲染 Markdown 轨迹。

    要求包含：
    - 标题含 goal
    - Policy 行：max_steps / streak / block_last
    - 每步 Step N · kind；Thought；若非 final 则 Fingerprint / Action / Observation
    - 结尾 Stopped + Final
    """
    # TODO: 实现
    raise NotImplementedError
