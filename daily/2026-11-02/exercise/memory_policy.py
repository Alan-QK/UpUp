"""Day 64 练习：记忆写入策略（何时写入长期记忆）。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——不调用 LLM，不做真实持久化。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

ACTION_WRITE = "write"
ACTION_SKIP = "skip"
ACTION_ASK = "ask"
VALID_ACTIONS = frozenset({ACTION_WRITE, ACTION_SKIP, ACTION_ASK})

KIND_PREFERENCE = "preference"
KIND_FACT = "fact"
KIND_NOTE = "note"
KIND_NONE = "none"
VALID_KINDS = frozenset({KIND_PREFERENCE, KIND_FACT, KIND_NOTE, KIND_NONE})

ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_SYSTEM = "system"
VALID_ROLES = frozenset({ROLE_USER, ROLE_ASSISTANT, ROLE_SYSTEM})

MIN_TEXT_LEN = 2

REQUIRED_REPORT_SECTIONS = (
    "何为记忆写入策略",
    "启发式决策顺序",
    "今日演示统计",
    "与长期记忆衔接",
    "明日预告",
)

# 以下正则已给齐，启发式请直接复用，勿改语义。
_EXPLICIT_REMEMBER = re.compile(
    r"(请记住|记住这|帮我记住|别忘了|以后都|下次都|remember\s+(this|that|to)|don't forget)",
    re.IGNORECASE,
)
_EXPLICIT_FORGET = re.compile(
    r"(不要记住|别记住|忘掉这个|不要存|forget\s+this|do\s+not\s+remember)",
    re.IGNORECASE,
)
_PREFERENCE_RE = re.compile(
    r"(我喜欢|我不喜欢|我偏好|我更喜欢|更喜欢|请用.+回答|请用.+写|不要给我|别用|我习惯|优先使用)",
    re.IGNORECASE,
)
_FACT_RE = re.compile(
    r"(我叫|我的名字是|我是.+工程师|我在.+工作|我的时区|时区是|我住在)",
    re.IGNORECASE,
)
_EPHEMERAL_RE = re.compile(
    r"^(你好|您好|嗨|在吗|谢谢|感谢|哈哈|嗯+|好的|ok|okay|早上好|晚安)[\s!！。.~～]*$",
    re.IGNORECASE,
)
_SENSITIVE_RE = re.compile(
    r"(password|passwd|密码|api[_\s-]?key|secret[_\s-]?key|"
    r"sk-[a-z0-9]{10,}|"
    r"1[3-9]\d{9}|"
    r"\d{17}[\dXx])",
    re.IGNORECASE,
)
_HEDGE_RE = re.compile(r"(可能|也许|大概|暂时|先试试|不确定)", re.IGNORECASE)


@dataclass(frozen=True)
class MemoryDecision:
    """一条话语的写入决策。"""

    text: str
    action: str
    kind: str
    reason: str
    confidence: float
    normalized_text: str
    role: str = ROLE_USER

    def __post_init__(self) -> None:
        if self.action not in VALID_ACTIONS:
            raise ValueError(f"invalid action: {self.action}")
        if self.kind not in VALID_KINDS:
            raise ValueError(f"invalid kind: {self.kind}")
        if self.role not in VALID_ROLES:
            raise ValueError(f"invalid role: {self.role}")
        if not isinstance(self.confidence, (int, float)):
            raise TypeError("confidence must be number")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence out of range")


@dataclass(frozen=True)
class PolicyStats:
    """一次批量决策的统计。"""

    total: int
    write_count: int
    skip_count: int
    ask_count: int
    by_kind: dict[str, int]


def normalize_candidate(text: str) -> str:
    """清洗待写入文本：去首尾空白、压缩连续空白。"""
    # TODO: 非 str 抛 TypeError；strip + 把连续空白压成单个空格
    raise NotImplementedError


def contains_sensitive(text: str) -> bool:
    """是否命中敏感模式（密码 / Key / 手机号等）。"""
    # TODO: 非 str 抛 TypeError；用 _SENSITIVE_RE.search
    raise NotImplementedError


def decide_write(text: str, *, role: str = ROLE_USER) -> MemoryDecision:
    """对单条消息做写入决策（规则启发式，不调用 LLM）。

    决策顺序（从前到后，命中即返回）：
    1. 非 user → SKIP / reason=non_user_role / confidence=1.0
    2. 空字符串（normalize 后）→ SKIP / too_short / 1.0
    3. 敏感 → SKIP / sensitive / 1.0
    4. 显式勿记 → SKIP / explicit_forget / 0.95
    5. 显式请记 → WRITE；若同时有偏好信号则 kind=preference 否则 note；
       reason=explicit_remember / confidence=0.95
    6. 寒暄 → SKIP / ephemeral / 0.9
    7. 长度 < MIN_TEXT_LEN → SKIP / too_short / 1.0
    8. 偏好信号：
       - 含犹豫词 → ASK / preference / preference_hedged / 0.55
       - 否则 → WRITE / preference / preference_signal / 0.85
    9. 事实信号 → WRITE / fact / fact_signal / 0.8
    10. 默认 → SKIP / none / no_signal / 0.7

    所有返回的 normalized_text 都应是 normalize_candidate(text) 的结果。
    text 原样保留在 MemoryDecision.text。
    """
    # TODO
    raise NotImplementedError


def decide_batch(messages: Sequence[tuple[str, str]]) -> list[MemoryDecision]:
    """批量决策。messages: (role, content) 列表。"""
    # TODO: 校验类型；逐条调用 decide_write
    raise NotImplementedError


def filter_writable(decisions: Sequence[MemoryDecision]) -> list[MemoryDecision]:
    """只保留 action=write 的决策。"""
    # TODO
    raise NotImplementedError


def summarize_decisions(decisions: Sequence[MemoryDecision]) -> PolicyStats:
    """汇总统计。"""
    # TODO: 统计 write/skip/ask 与 by_kind
    raise NotImplementedError


def build_demo_utterances() -> list[tuple[str, str]]:
    """演示用 (role, text) 列表（已给齐，勿改顺序与文案）。"""
    return [
        (ROLE_USER, "你好"),
        (ROLE_USER, "请记住：以后都用中文回答我"),
        (ROLE_USER, "我喜欢深色主题，少一点动画"),
        (ROLE_USER, "我可能更喜欢浅色，不确定"),
        (ROLE_USER, "我叫小凯，是一名前端工程师"),
        (ROLE_USER, "我的密码是 Secret123，别告诉别人"),
        (ROLE_USER, "帮我看看这段按钮样式怎么改"),
        (ROLE_USER, "不要记住刚才那句闲聊"),
        (ROLE_ASSISTANT, "好的，已记下你的偏好"),
        (ROLE_USER, "谢谢"),
    ]


def run_demo_policy() -> tuple[list[MemoryDecision], PolicyStats]:
    """跑一遍演示语料。"""
    # TODO: decide_batch(build_demo_utterances()) + summarize_decisions
    raise NotImplementedError


def render_memory_policy_report(
    decisions: Sequence[MemoryDecision],
    stats: PolicyStats | None = None,
) -> str:
    """生成 Markdown 报告，必须包含 REQUIRED_REPORT_SECTIONS 全部二级标题。"""
    # TODO
    raise NotImplementedError
