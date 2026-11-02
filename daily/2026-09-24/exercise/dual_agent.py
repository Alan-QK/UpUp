"""Day 45 练习：双工具 Agent（时间 + 计算器）周挑战。

请完成 TODO，使 tests/ 全部通过。
toolkit / roundtrip 已给齐，可直接 import。
全程只用标准库。
"""

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

# 规划启发式用的关键词（可按需微调，但测试会覆盖这些）
_TIME_HINTS = ("几点", "时间", "时区", "现在", "今天", "日期", "timezone", "utc")
_CALC_HINTS = ("算", "计算", "等于", "加", "减", "乘", "除")
_EXPR_RE = re.compile(r"[\d]+(?:\s*[+\-*/()]\s*[\d]+)+")
_TZ_RE = re.compile(
    r"\b(?:UTC|GMT|Asia/Shanghai|America/New_York|Europe/London)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AgentResult:
    """双工具 Agent 一次运行的结果。"""

    user_text: str
    messages: list[dict[str, Any]]
    final_content: str
    tool_names: list[str]
    used_tools: bool


def default_system_prompt() -> str:
    """返回 system 提示（已实现，可直接用）。"""
    names = "、".join(DUAL_TOOL_NAMES)
    return (
        "你是一个只拥有两个工具的助手："
        f"{names}。"
        "需要精确数值时调用 calculate；需要当前时刻时调用 get_current_time。"
        "可以在同一轮并行调用多个工具。不要编造计算结果或时间。"
    )


def last_user_content(messages: list[dict[str, Any]]) -> str:
    """从后往前找最后一条 role=user 的 content。

    规则：
    - messages 必须是 list，否则 ValueError("messages must be a list")
    - 找到则返回 str(content)（content 为 None → ""）
    - 找不到 → ValueError("no user message")
    """
    # TODO: 实现
    raise NotImplementedError


def needs_current_time(text: str) -> bool:
    """用户是否在问时间？

    规则：把 text 转小写后，若包含 _TIME_HINTS 任一子串 → True，否则 False。
    空/纯空白 → False。
    """
    # TODO: 实现
    raise NotImplementedError


def needs_calculate(text: str) -> bool:
    """用户是否在要求计算？

    规则：
    - 空/纯空白 → False
    - 若包含 _CALC_HINTS 任一子串 → True
    - 或能用 extract_expression 抽到表达式 → True
    - 否则 False
    """
    # TODO: 实现
    raise NotImplementedError


def extract_expression(text: str) -> str | None:
    """从用户话里抽出算术表达式。

    规则（按优先级）：
    1. 若包含「算一下」或「计算」，取其后片段；去掉首尾空白与中文标点（。？！；,，）；
       若剩余非空且看起来像表达式（含数字），去掉内部空白后返回
    2. 否则用 _EXPR_RE 在全文找第一处匹配，去掉空白后返回
    3. 找不到 → None

    注意：不要 eval；只做字符串抽取。
    """
    # TODO: 实现
    raise NotImplementedError


def extract_timezone(text: str) -> str:
    """抽出时区；默认 UTC。

    规则：
    - 用 _TZ_RE 找第一处；命中则返回原文中的标准写法：
      utc/gmt → UTC；asia/shanghai → Asia/Shanghai；
      america/new_york → America/New_York；europe/london → Europe/London
    - 若包含「上海」但没匹配到 IANA → Asia/Shanghai
    - 否则 → "UTC"
    """
    # TODO: 实现
    raise NotImplementedError


def plan_tool_calls(user_text: str) -> list[dict[str, Any]]:
    """根据用户话规划 tool_calls 列表（可为空、可并行）。

    规则：
    - 顺序固定：若需要时间，先 append get_current_time（id=call_time）；
      若需要计算，再 append calculate（id=call_calc）
    - get_current_time arguments：{"timezone": extract_timezone(user_text)}
    - calculate：必须 extract_expression 成功；arguments={"expression": expr}
      若 needs_calculate 但抽不出表达式 → 不挂 calculate（宁可少调，别瞎调）
    - 每条 tool_call 结构：
      {"id", "type":"function", "function":{"name", "arguments": <JSON 字符串>}}
    - arguments JSON 用 json.dumps(..., ensure_ascii=False, separators=(",", ":"))
    """
    # TODO: 实现
    raise NotImplementedError


def synthesize_direct(user_text: str) -> str:
    """无工具时的直接回答（已实现，可直接用）。"""
    text = " ".join(user_text.split())
    if not text:
        return "你好，我可以帮你看时间和做计算。"
    return f"我是双工具助手，目前只能查时间或做计算。你刚才说：{text}"


def synthesize_answer(
    user_text: str,
    tool_messages: list[dict[str, Any]],
) -> str:
    """根据 tool 回执拼最终自然语言。

    规则：
    - 遍历 tool_messages（已是执行顺序）
    - content 以 ERROR: 开头 → 追加「工具失败：{content}」
    - 否则尝试 json.loads：
        * 含 datetime → 「{timezone} 当前时间：{datetime}」
        * 含 result → 「{expression} = {result}」
        * 其它 dict → 把紧凑 JSON 原文追加
      解析失败 → 把 content 原文追加
    - 多段用中文分号「；」连接
    - 若 tool_messages 为空 → 退回 synthesize_direct(user_text)
    """
    # TODO: 实现
    raise NotImplementedError


class HeuristicChat:
    """离线假模型：第 1 轮规划工具，第 2 轮根据 tool 结果回答。

    要求：
    - self.calls: list，每次 __call__ 先 append deepcopy(messages)
    - 第 1 次：plan_tool_calls(last_user_content(messages))
        * 非空 → {"role":"assistant","content":None,"tool_calls":...}
        * 空 → {"role":"assistant","content": synthesize_direct(...)}
    - 第 2 次及以后：收集 messages 里 role==tool 的条目，
      返回 {"role":"assistant","content": synthesize_answer(user, tool_msgs)}
    - 计数用实例状态；不要用全局变量
    """

    def __init__(self) -> None:
        self.calls: list[list[dict[str, Any]]] = []
        self._round = 0

    def __call__(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        # TODO: 实现
        raise NotImplementedError


def tool_names_from_messages(messages: list[dict[str, Any]]) -> list[str]:
    """按出现顺序提取 assistant.tool_calls 里的工具名（去重保留顺序）。

    规则：
    - 只看 role==assistant 且带非空 tool_calls 的消息
    - 名称为 function.name；缺省跳过
    - 同一名字只保留第一次
    """
    # TODO: 实现
    raise NotImplementedError


def run_dual_agent(
    user_text: str,
    chat: ChatFn | None = None,
) -> AgentResult:
    """运行一次双工具 Agent。

    流程：
    1. user_text 必须是 str，否则 ValueError("user_text must be str")
    2. history = [
         {"role":"system","content": default_system_prompt()},
         {"role":"user","content": user_text},
       ]
    3. chat_fn = chat if chat is not None else HeuristicChat()
    4. rt = run_tool_roundtrip(history, chat_fn, execute=execute_dual_tools)
    5. 返回 AgentResult(
         user_text=user_text,
         messages=rt.messages,
         final_content=rt.final_content,
         tool_names=tool_names_from_messages(rt.messages),
         used_tools=rt.used_tools,
       )
    """
    # TODO: 实现
    raise NotImplementedError


def render_agent_markdown(result: AgentResult) -> str:
    """渲染 Agent 摘要（已实现，可直接用）。"""
    lines = [
        "# Dual Tool Agent",
        f"user：{result.user_text}",
        f"used_tools：{'yes' if result.used_tools else 'no'}",
        f"tools：{', '.join(result.tool_names) if result.tool_names else '(none)'}",
        "## Final",
        result.final_content if result.final_content else "(empty)",
    ]
    # 提醒读者 toolkit 契约仍在
    _ = dual_toolkit
    _ = RoundTripResult
    _ = Callable
    return "\n".join(lines)
