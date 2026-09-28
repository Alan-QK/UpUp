"""Day 45 参考实现：双工具 Agent（时间 + 计算器）。"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from typing import Any, Callable

from roundtrip import ChatFn, RoundTripResult, run_tool_roundtrip
from toolkit import (
    DUAL_TOOL_NAMES,
    dual_toolkit,
    execute_dual_tools,
)

_TIME_HINTS = ("几点", "时间", "时区", "现在", "今天", "日期", "timezone", "utc")
_CALC_HINTS = ("算", "计算", "等于", "加", "减", "乘", "除")
_EXPR_RE = re.compile(r"[\d]+(?:\s*[+\-*/()]\s*[\d]+)+")
_TZ_RE = re.compile(
    r"\b(?:UTC|GMT|Asia/Shanghai|America/New_York|Europe/London)\b",
    re.IGNORECASE,
)

_TZ_CANON = {
    "utc": "UTC",
    "gmt": "UTC",
    "asia/shanghai": "Asia/Shanghai",
    "america/new_york": "America/New_York",
    "europe/london": "Europe/London",
}


@dataclass(frozen=True)
class AgentResult:
    """双工具 Agent 一次运行的结果。"""

    user_text: str
    messages: list[dict[str, Any]]
    final_content: str
    tool_names: list[str]
    used_tools: bool


def default_system_prompt() -> str:
    """返回 system 提示。"""
    names = "、".join(DUAL_TOOL_NAMES)
    return (
        "你是一个只拥有两个工具的助手："
        f"{names}。"
        "需要精确数值时调用 calculate；需要当前时刻时调用 get_current_time。"
        "可以在同一轮并行调用多个工具。不要编造计算结果或时间。"
    )


def last_user_content(messages: list[dict[str, Any]]) -> str:
    """从后往前找最后一条 role=user 的 content。"""
    if not isinstance(messages, list):
        raise ValueError("messages must be a list")
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            content = message.get("content")
            if content is None:
                return ""
            return str(content)
    raise ValueError("no user message")


def needs_current_time(text: str) -> bool:
    """用户是否在问时间？"""
    lowered = text.lower()
    if not text.strip():
        return False
    return any(hint in lowered for hint in _TIME_HINTS)


def needs_calculate(text: str) -> bool:
    """用户是否在要求计算？"""
    if not text.strip():
        return False
    if any(hint in text for hint in _CALC_HINTS):
        return True
    return extract_expression(text) is not None


def extract_expression(text: str) -> str | None:
    """从用户话里抽出算术表达式。"""
    for hint in ("算一下", "计算"):
        if hint in text:
            tail = text.split(hint, 1)[1]
            tail = tail.strip().strip("。？！；,，、")
            compact = re.sub(r"\s+", "", tail)
            if compact and re.search(r"\d", compact):
                return compact

    match = _EXPR_RE.search(text)
    if match:
        return re.sub(r"\s+", "", match.group(0))
    return None


def extract_timezone(text: str) -> str:
    """抽出时区；默认 UTC。"""
    match = _TZ_RE.search(text)
    if match:
        return _TZ_CANON[match.group(0).lower()]
    if "上海" in text:
        return "Asia/Shanghai"
    return "UTC"


def plan_tool_calls(user_text: str) -> list[dict[str, Any]]:
    """根据用户话规划 tool_calls 列表（可为空、可并行）。"""
    calls: list[dict[str, Any]] = []

    if needs_current_time(user_text):
        args = {"timezone": extract_timezone(user_text)}
        calls.append(
            {
                "id": "call_time",
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "arguments": json.dumps(args, ensure_ascii=False, separators=(",", ":")),
                },
            }
        )

    if needs_calculate(user_text):
        expr = extract_expression(user_text)
        if expr:
            args = {"expression": expr}
            calls.append(
                {
                    "id": "call_calc",
                    "type": "function",
                    "function": {
                        "name": "calculate",
                        "arguments": json.dumps(
                            args, ensure_ascii=False, separators=(",", ":")
                        ),
                    },
                }
            )

    return calls


def synthesize_direct(user_text: str) -> str:
    """无工具时的直接回答。"""
    text = " ".join(user_text.split())
    if not text:
        return "你好，我可以帮你看时间和做计算。"
    return f"我是双工具助手，目前只能查时间或做计算。你刚才说：{text}"


def synthesize_answer(
    user_text: str,
    tool_messages: list[dict[str, Any]],
) -> str:
    """根据 tool 回执拼最终自然语言。"""
    if not tool_messages:
        return synthesize_direct(user_text)

    parts: list[str] = []
    for message in tool_messages:
        content = message.get("content", "")
        if not isinstance(content, str):
            content = str(content)
        if content.startswith("ERROR:"):
            parts.append(f"工具失败：{content}")
            continue
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            parts.append(content)
            continue
        if isinstance(data, dict) and "datetime" in data:
            tz = data.get("timezone", "UTC")
            parts.append(f"{tz} 当前时间：{data['datetime']}")
        elif isinstance(data, dict) and "result" in data:
            expr = data.get("expression", "?")
            parts.append(f"{expr} = {data['result']}")
        elif isinstance(data, dict):
            parts.append(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        else:
            parts.append(content)
    return "；".join(parts)


class HeuristicChat:
    """离线假模型：第 1 轮规划工具，第 2 轮根据 tool 结果回答。"""

    def __init__(self) -> None:
        self.calls: list[list[dict[str, Any]]] = []
        self._round = 0

    def __call__(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        self.calls.append(copy.deepcopy(messages))
        self._round += 1
        user_text = last_user_content(messages)

        if self._round == 1:
            tool_calls = plan_tool_calls(user_text)
            if not tool_calls:
                return {
                    "role": "assistant",
                    "content": synthesize_direct(user_text),
                }
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": tool_calls,
            }

        tool_msgs = [
            message
            for message in messages
            if isinstance(message, dict) and message.get("role") == "tool"
        ]
        return {
            "role": "assistant",
            "content": synthesize_answer(user_text, tool_msgs),
        }


def tool_names_from_messages(messages: list[dict[str, Any]]) -> list[str]:
    """按出现顺序提取 assistant.tool_calls 里的工具名（去重保留顺序）。"""
    names: list[str] = []
    seen: set[str] = set()
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        raw = message.get("tool_calls")
        if not isinstance(raw, list) or not raw:
            continue
        for item in raw:
            if not isinstance(item, dict):
                continue
            function = item.get("function")
            if not isinstance(function, dict):
                continue
            name = function.get("name")
            if not isinstance(name, str) or not name or name in seen:
                continue
            seen.add(name)
            names.append(name)
    return names


def run_dual_agent(
    user_text: str,
    chat: ChatFn | None = None,
) -> AgentResult:
    """运行一次双工具 Agent。"""
    if not isinstance(user_text, str):
        raise ValueError("user_text must be str")

    history = [
        {"role": "system", "content": default_system_prompt()},
        {"role": "user", "content": user_text},
    ]
    chat_fn: ChatFn = HeuristicChat() if chat is None else chat
    rt = run_tool_roundtrip(history, chat_fn, execute=execute_dual_tools)
    return AgentResult(
        user_text=user_text,
        messages=rt.messages,
        final_content=rt.final_content,
        tool_names=tool_names_from_messages(rt.messages),
        used_tools=rt.used_tools,
    )


def render_agent_markdown(result: AgentResult) -> str:
    """渲染 Agent 摘要。"""
    lines = [
        "# Dual Tool Agent",
        f"user：{result.user_text}",
        f"used_tools：{'yes' if result.used_tools else 'no'}",
        f"tools：{', '.join(result.tool_names) if result.tool_names else '(none)'}",
        "## Final",
        result.final_content if result.final_content else "(empty)",
    ]
    _ = dual_toolkit
    _ = RoundTripResult
    _ = Callable
    return "\n".join(lines)
