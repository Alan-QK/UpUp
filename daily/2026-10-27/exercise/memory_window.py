"""Day 61 练习：增强历史窗口（短时会话记忆）。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——不调用真实 LLM，不做向量检索。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

ROLE_SYSTEM = "system"
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_TOOL = "tool"
VALID_ROLES = frozenset({ROLE_SYSTEM, ROLE_USER, ROLE_ASSISTANT, ROLE_TOOL})

REQUIRED_REPORT_SECTIONS = (
    "何为短记忆",
    "增强策略",
    "与 Day16 对比",
    "今日演示统计",
    "明日预告",
)


@dataclass(frozen=True)
class ChatTurn:
    """一条会话消息。"""

    role: str
    content: str
    pinned: bool = False

    def __post_init__(self) -> None:
        if self.role not in VALID_ROLES:
            raise ValueError(f"invalid role: {self.role}")
        if not isinstance(self.content, str):
            raise TypeError("content must be str")


@dataclass(frozen=True)
class WindowStats:
    """一次裁剪的统计。"""

    input_messages: int
    kept_messages: int
    dropped_messages: int
    estimated_tokens_kept: int
    estimated_tokens_dropped: int
    max_turns: int | None
    max_tokens: int | None
    pinned_kept: int
    system_kept: int


@dataclass(frozen=True)
class WindowResult:
    """增强窗口的输出。"""

    messages: list[ChatTurn]
    dropped: list[ChatTurn]
    stats: WindowStats


def estimate_tokens(text: str) -> int:
    """教学用启发式：空串返回 0；否则 max(1, (len(text) + 3) // 4)。"""
    # TODO: 实现估算；非 str 抛 TypeError
    raise NotImplementedError


def message_tokens(msg: ChatTurn) -> int:
    """单条消息估 token = estimate_tokens(content) + 1（role 开销）。"""
    # TODO
    raise NotImplementedError


def count_exchange_turns(messages: Sequence[ChatTurn]) -> int:
    """统计完整 user+assistant 轮数（一对 = 1 轮）。"""
    # TODO
    raise NotImplementedError


def apply_enhanced_window(
    messages: Sequence[ChatTurn],
    *,
    max_turns: int | None = None,
    max_tokens: int | None = None,
    keep_system: bool = True,
) -> WindowResult:
    """增强窗口裁剪，不修改入参。

    规则概要：
    1. 必须提供 max_turns 和/或 max_tokens；非法值（<1）→ ValueError
    2. keep_system 时保留所有 system；pinned=True 一律保留
    3. 其余只保留完整 user+assistant 轮；从新到旧选取
    4. 仅 max_turns：留最近 N 轮（外加保护项）
    5. 有 max_tokens：保护项先占预算，再从新到旧装入整轮，超了就停
    6. 两者都有：先按轮数得到候选，再按预算装入
    7. 非保护的孤立消息（落单 user / tool 等）默认丢弃
    8. 返回 WindowResult，并填满 WindowStats
    """
    # TODO
    raise NotImplementedError


class SessionMemory:
    """短时会话记忆：追加后按策略裁剪。"""

    def __init__(
        self,
        *,
        max_turns: int | None = 3,
        max_tokens: int | None = None,
        keep_system: bool = True,
        system_prompt: str | None = None,
    ) -> None:
        # TODO: 校验参数；可选写入初始 system 消息
        raise NotImplementedError

    @property
    def max_turns(self) -> int | None:
        # TODO
        raise NotImplementedError

    @property
    def max_tokens(self) -> int | None:
        # TODO
        raise NotImplementedError

    def add(self, role: str, content: str, *, pinned: bool = False) -> None:
        """追加一条消息并立即按窗口策略裁剪。"""
        # TODO
        raise NotImplementedError

    def add_exchange(self, user_text: str, assistant_text: str) -> None:
        """追加一轮完整 user+assistant 并裁剪。"""
        # TODO
        raise NotImplementedError

    def history(self) -> list[ChatTurn]:
        """返回历史副本。"""
        # TODO
        raise NotImplementedError

    def last_result(self) -> WindowResult | None:
        """最近一次裁剪结果；尚未裁剪过则为 None。"""
        # TODO
        raise NotImplementedError

    def reset(self, *, keep_system_messages: bool = True) -> None:
        """清空历史；可选择保留 system。"""
        # TODO
        raise NotImplementedError


def build_demo_transcript() -> list[ChatTurn]:
    """构造演示用多轮对话（含一条 pinned 偏好）。"""
    return [
        ChatTurn(role=ROLE_SYSTEM, content="你是前端转 Agent 的学习助理。"),
        ChatTurn(role=ROLE_USER, content="我叫小前端。请记住。", pinned=True),
        ChatTurn(role=ROLE_USER, content="什么是 Agent Loop？"),
        ChatTurn(role=ROLE_ASSISTANT, content="Loop 是模型与工具多轮交替直到结束。"),
        ChatTurn(role=ROLE_USER, content="Guard 是什么？"),
        ChatTurn(role=ROLE_ASSISTANT, content="Guard 是工具调用前的硬门禁。"),
        ChatTurn(role=ROLE_USER, content="HITL 呢？"),
        ChatTurn(role=ROLE_ASSISTANT, content="HITL 是危险操作前的人机确认。"),
        ChatTurn(role=ROLE_USER, content="短记忆和长期记忆差别？"),
        ChatTurn(role=ROLE_ASSISTANT, content="短记忆在窗口内；长期记忆跨会话召回。"),
    ]


def render_window_report(result: WindowResult) -> str:
    """生成 Markdown 报告，必须包含 REQUIRED_REPORT_SECTIONS 里的二级标题。"""
    # TODO
    raise NotImplementedError
