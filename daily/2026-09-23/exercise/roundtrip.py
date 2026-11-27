"""Day 44 练习：工具结果回填多轮（消息协议 + 再问模型）。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库。mini_executor 已给齐，可直接 import。
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Callable

from mini_executor import (
    execute_assistant_tool_calls,
    extract_tool_calls,
    to_tool_messages,
)

ChatFn = Callable[[list[dict[str, Any]]], dict[str, Any]]
ExecuteFn = Callable[[dict[str, Any]], list[dict[str, Any]]]


@dataclass(frozen=True)
class RoundTripResult:
    """一轮（或零轮）工具回填后的结果。"""

    messages: list[dict[str, Any]]
    final_content: str
    tool_messages: list[dict[str, Any]]
    used_tools: bool


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


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白（含换行）压成单个空格。"""
    # TODO: 实现规范化
    raise NotImplementedError


def has_tool_calls(assistant_message: dict[str, Any]) -> bool:
    """是否包含至少一条 tool_call。

    规则：
    - 不是 dict → False
    - tool_calls 缺失 / None / 非 list / 空 list → False
    - 否则 True
    """
    # TODO: 实现
    raise NotImplementedError


def extract_tool_call_ids(assistant_message: dict[str, Any]) -> list[str]:
    """按顺序取出 tool_calls[].id（normalize_text 后）。

    规则：
    - 若无 tool_calls（同 has_tool_calls=False）→ 返回 []
    - 若某条缺 id 或 normalize 后为空 → ValueError("tool_call id must be non-empty")
    - 不在这里校验 type/function（那是执行器的事）；只抽 id
    - 每条 raw 必须是 dict，否则 ValueError("tool_call must be a dict")
    """
    # TODO: 实现
    raise NotImplementedError


def validate_tool_message(message: dict[str, Any]) -> None:
    """校验单条 role=tool 消息。

    规则：
    - 必须是 dict
    - role 必须等于 "tool"
    - tool_call_id 经 normalize_text 后非空
    - content 必须是 str（允许空字符串；失败文案也是 str）
    - 否则抛 ValueError，消息里带上字段名线索（role / tool_call_id / content）
    """
    # TODO: 实现
    raise NotImplementedError


def validate_tool_followup(
    assistant_message: dict[str, Any],
    tool_messages: list[dict[str, Any]],
) -> None:
    """校验 tool 回填是否与 assistant.tool_calls 一一对应且顺序一致。

    规则：
    - assistant 必须 has_tool_calls，否则 ValueError("assistant has no tool_calls")
    - tool_messages 必须是 list
    - len(tool_messages) 必须等于 len(tool_calls)，否则 ValueError("tool message count mismatch")
    - 对每个下标 i：先 validate_tool_message；再要求
      normalize_text(tool_messages[i]["tool_call_id"]) == extract_tool_call_ids(...)[i]
      不一致 → ValueError("tool_call_id mismatch")
    """
    # TODO: 实现
    raise NotImplementedError


def build_messages_after_tools(
    history: list[dict[str, Any]],
    assistant_message: dict[str, Any],
    tool_messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """拼接：history + assistant + tool* ，返回新列表。

    规则：
    - 先 validate_tool_followup(assistant_message, tool_messages)
    - history 必须是 list，否则 ValueError("history must be a list")
    - 返回 deepcopy 后的新列表；修改返回值 / 其中元素 **不得**影响入参
    - 不在这里调用模型
    """
    # TODO: 实现
    raise NotImplementedError


def default_execute(assistant_message: dict[str, Any]) -> list[dict[str, Any]]:
    """默认执行器：复用 mini_executor，产出 role=tool 列表。"""
    results = execute_assistant_tool_calls(assistant_message)
    return to_tool_messages(results)


def finalize_content(assistant_message: dict[str, Any]) -> str:
    """从最终 assistant 消息取出 content 字符串。

    规则：
    - 若仍 has_tool_calls → ValueError("expected final answer without tool_calls")
    - content 为 None → 返回 ""
    - content 为 str → 原样返回（不做 strip）
    - 其它类型 → ValueError("final content must be str or None")
    """
    # TODO: 实现
    raise NotImplementedError


def run_tool_roundtrip(
    history: list[dict[str, Any]],
    chat: ChatFn,
    *,
    execute: ExecuteFn | None = None,
) -> RoundTripResult:
    """执行「至多一轮」工具回填，再拿最终回答。

    流程：
    1. history 必须是 list，否则 ValueError("history must be a list")
    2. first = chat(deepcopy(history))；first 必须是 dict，否则 ValueError("chat must return a dict")
    3. 若 not has_tool_calls(first):
         messages = deepcopy(history) + [deepcopy(first)]
         返回 RoundTripResult(messages, finalize_content(first), [], False)
    4. 否则：
         exec_fn = execute or default_execute
         tool_msgs = exec_fn(first)
         若 tool_msgs 不是 list → ValueError("execute must return a list")
         next_messages = build_messages_after_tools(history, first, tool_msgs)
         second = chat(deepcopy(next_messages))
         second 必须是 dict
         final_messages = next_messages + [deepcopy(second)]
         返回 RoundTripResult(
             final_messages,
             finalize_content(second),  # 若 second 仍有 tool_calls，这里会 ValueError
             copy.deepcopy(tool_msgs),
             True,
         )

    注意：传给 chat 的 list 用 deepcopy，避免脚本/单测里被原地修改污染。
    """
    # TODO: 实现编排
    raise NotImplementedError


def render_roundtrip_markdown(result: RoundTripResult) -> str:
    """渲染回合摘要（已实现，可直接用）。"""
    lines = [
        "# Tool Roundtrip",
        f"used_tools：{'yes' if result.used_tools else 'no'}",
        f"tool_count：{len(result.tool_messages)}",
        "## Final",
        result.final_content if result.final_content else "(empty)",
    ]
    if result.tool_messages:
        lines.append("## Tool Messages")
        for item in result.tool_messages:
            lines.append(f"- {item.get('tool_call_id')}: {item.get('content')}")
    # 静默引用 extract_tool_calls，提醒读者协议与执行器的关系
    _ = extract_tool_calls
    return "\n".join(lines)
