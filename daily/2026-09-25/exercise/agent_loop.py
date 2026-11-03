"""Day 46 练习：手写最小 ReAct / Agent Loop。

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
    """返回 system 提示（已实现，可直接用）。"""
    names = "、".join(item["function"]["name"] for item in loop_toolkit())
    return (
        "你是 ReAct 风格助手，遵循 Thought → Action → Observation 循环。"
        f"可用工具：{names}。"
        "需要事实时先 lookup；需要精确运算时 calculate。"
        "信息足够后直接给出最终回答，不要再调用工具。"
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
    """抽取 Thought 文本（即 assistant.content）。

    规则：
    - 非 dict → ""
    - content 为 None → ""
    - 否则返回 normalize_text(str(content))
    """
    # TODO: 实现
    raise NotImplementedError


def validate_max_steps(max_steps: int) -> int:
    """校验 max_steps。

    规则：
    - 必须是 int（bool 不算），否则 ValueError("max_steps must be int")
    - 必须 >= 1，否则 ValueError("max_steps must be >= 1")
    - 返回原值
    """
    # TODO: 实现
    raise NotImplementedError


def run_agent_loop(
    goal: str,
    chat: ChatFn,
    *,
    execute: ExecuteFn | None = None,
    system_prompt: str | None = None,
    max_steps: int = 6,
) -> LoopResult:
    """手写最小 Agent Loop。

    流程：
    1. validate_max_steps；goal 经 normalize_text 后不得为空，否则
       ValueError("goal must be non-empty")
    2. execute 默认 execute_assistant_tools；system 默认 default_system_prompt()
    3. messages = [system, user(goal)]（深拷贝无关，内部新建即可）
    4. for index in 1..max_steps:
         - assistant = chat(messages)；必须是 dict，否则 ValueError("chat must return dict")
         - 将 assistant 的深拷贝 append 进 messages
         - 若无 tool_calls：记一步 kind="final"，stopped_reason=final_answer，
           final_content=assistant_thought(assistant)（可为空字符串），返回
         - 否则：tool_msgs = execute(assistant)；必须是 list，否则
           ValueError("execute must return list")
           把每条 tool 消息深拷贝后 append；记一步 kind="action"
    5. 若循环结束仍未 final：stopped_reason=max_steps，
       final_content="(stopped: max_steps)"

    注意：
    - step_count == len(steps)
    - 不要修改传入的 chat / execute 闭包之外的外部列表（ScriptedChat.calls 除外）
    """
    # TODO: 实现
    raise NotImplementedError


def render_trace_markdown(result: LoopResult) -> str:
    """把 LoopResult 渲染成便于阅读的 Markdown 轨迹。

    要求包含：
    - 标题行含 goal
    - 每一步：Step N · action|final
    - Thought 行、若有工具则 Action / Observation 行
    - 结尾：Stopped: <reason> 与 Final: <content>
    """
    # TODO: 实现
    raise NotImplementedError
