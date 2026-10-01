"""Day 44 参考实现：工具结果回填多轮。"""

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
    return " ".join(text.split())


def has_tool_calls(assistant_message: dict[str, Any]) -> bool:
    """是否包含至少一条 tool_call。"""
    if not isinstance(assistant_message, dict):
        return False
    raw = assistant_message.get("tool_calls")
    return isinstance(raw, list) and len(raw) > 0


def extract_tool_call_ids(assistant_message: dict[str, Any]) -> list[str]:
    """按顺序取出 tool_calls[].id（normalize_text 后）。"""
    if not has_tool_calls(assistant_message):
        return []
    ids: list[str] = []
    for item in assistant_message["tool_calls"]:
        if not isinstance(item, dict):
            raise ValueError("tool_call must be a dict")
        call_id = normalize_text(str(item.get("id", "")))
        if not call_id:
            raise ValueError("tool_call id must be non-empty")
        ids.append(call_id)
    return ids


def validate_tool_message(message: dict[str, Any]) -> None:
    """校验单条 role=tool 消息。"""
    if not isinstance(message, dict):
        raise ValueError("tool message must be a dict")
    if message.get("role") != "tool":
        raise ValueError("tool message role must be tool")
    call_id = normalize_text(str(message.get("tool_call_id", "")))
    if not call_id:
        raise ValueError("tool_call_id must be non-empty")
    if not isinstance(message.get("content"), str):
        raise ValueError("tool message content must be str")


def validate_tool_followup(
    assistant_message: dict[str, Any],
    tool_messages: list[dict[str, Any]],
) -> None:
    """校验 tool 回填是否与 assistant.tool_calls 一一对应且顺序一致。"""
    if not has_tool_calls(assistant_message):
        raise ValueError("assistant has no tool_calls")
    if not isinstance(tool_messages, list):
        raise ValueError("tool_messages must be a list")
    expected_ids = extract_tool_call_ids(assistant_message)
    if len(tool_messages) != len(expected_ids):
        raise ValueError("tool message count mismatch")
    for index, tool_msg in enumerate(tool_messages):
        validate_tool_message(tool_msg)
        actual_id = normalize_text(str(tool_msg.get("tool_call_id", "")))
        if actual_id != expected_ids[index]:
            raise ValueError("tool_call_id mismatch")


def build_messages_after_tools(
    history: list[dict[str, Any]],
    assistant_message: dict[str, Any],
    tool_messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """拼接：history + assistant + tool* ，返回新列表。"""
    validate_tool_followup(assistant_message, tool_messages)
    if not isinstance(history, list):
        raise ValueError("history must be a list")
    return [
        *copy.deepcopy(history),
        copy.deepcopy(assistant_message),
        *copy.deepcopy(tool_messages),
    ]


def default_execute(assistant_message: dict[str, Any]) -> list[dict[str, Any]]:
    """默认执行器：复用 mini_executor，产出 role=tool 列表。"""
    results = execute_assistant_tool_calls(assistant_message)
    return to_tool_messages(results)


def finalize_content(assistant_message: dict[str, Any]) -> str:
    """从最终 assistant 消息取出 content 字符串。"""
    if has_tool_calls(assistant_message):
        raise ValueError("expected final answer without tool_calls")
    content = assistant_message.get("content")
    if content is None:
        return ""
    if not isinstance(content, str):
        raise ValueError("final content must be str or None")
    return content


def run_tool_roundtrip(
    history: list[dict[str, Any]],
    chat: ChatFn,
    *,
    execute: ExecuteFn | None = None,
) -> RoundTripResult:
    """执行「至多一轮」工具回填，再拿最终回答。"""
    if not isinstance(history, list):
        raise ValueError("history must be a list")

    first = chat(copy.deepcopy(history))
    if not isinstance(first, dict):
        raise ValueError("chat must return a dict")

    if not has_tool_calls(first):
        messages = [*copy.deepcopy(history), copy.deepcopy(first)]
        return RoundTripResult(
            messages=messages,
            final_content=finalize_content(first),
            tool_messages=[],
            used_tools=False,
        )

    exec_fn = default_execute if execute is None else execute
    tool_msgs = exec_fn(first)
    if not isinstance(tool_msgs, list):
        raise ValueError("execute must return a list")

    next_messages = build_messages_after_tools(history, first, tool_msgs)
    second = chat(copy.deepcopy(next_messages))
    if not isinstance(second, dict):
        raise ValueError("chat must return a dict")

    final_messages = [*next_messages, copy.deepcopy(second)]
    return RoundTripResult(
        messages=final_messages,
        final_content=finalize_content(second),
        tool_messages=copy.deepcopy(tool_msgs),
        used_tools=True,
    )


def render_roundtrip_markdown(result: RoundTripResult) -> str:
    """渲染回合摘要。"""
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
    _ = extract_tool_calls
    return "\n".join(lines)
