"""Day 62 练习：摘要记忆（超长对话自动折叠）。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——不调用真实 LLM，不做向量检索。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

ROLE_SYSTEM = "system"
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
VALID_ROLES = frozenset({ROLE_SYSTEM, ROLE_USER, ROLE_ASSISTANT})

SUMMARY_MARKER = "[对话摘要]"

REQUIRED_REPORT_SECTIONS = (
    "何为摘要记忆",
    "滚动合并策略",
    "与短窗口对比",
    "今日演示统计",
    "明日预告",
)

# (user_text, assistant_text)
Exchange = tuple[str, str]
Summarizer = Callable[[Sequence[Exchange], str | None], str]


@dataclass(frozen=True)
class ChatTurn:
    """一条会话消息。"""

    role: str
    content: str

    def __post_init__(self) -> None:
        if self.role not in VALID_ROLES:
            raise ValueError(f"invalid role: {self.role}")
        if not isinstance(self.content, str):
            raise TypeError("content must be str")


@dataclass(frozen=True)
class CompactStats:
    """一次压缩的统计。"""

    input_exchanges: int
    kept_recent_exchanges: int
    folded_exchanges: int
    summary_chars: int
    estimated_tokens_context: int
    keep_recent_turns: int


@dataclass(frozen=True)
class CompactResult:
    """压缩后的上下文。"""

    messages: list[ChatTurn]
    folded: list[Exchange]
    summary_text: str | None
    stats: CompactStats


def estimate_tokens(text: str) -> int:
    """教学用启发式：空串返回 0；否则 max(1, (len(text) + 3) // 4)。"""
    # TODO: 实现估算；非 str 抛 TypeError
    raise NotImplementedError


def format_summary_message(summary: str) -> ChatTurn:
    """把摘要文本包装成 system 消息（必须以 SUMMARY_MARKER 开头）。"""
    # TODO
    raise NotImplementedError


def is_summary_message(msg: ChatTurn) -> bool:
    """判断是否为摘要 system 消息。"""
    # TODO
    raise NotImplementedError


def default_summarize(
    exchanges: Sequence[Exchange],
    previous_summary: str | None = None,
) -> str:
    """确定性 mock 摘要器（测试用）。

    规则：
    1. exchanges 为空 → ValueError
    2. 每轮变成一行：`- 用户：{截断} → 助手：{截断}`（单行，超 40 字符截断加 ...）
    3. 若 previous_summary 非空：先保留其 strip 后正文，再追加标题 `近期折叠：` 与新子弹
    4. 若无 previous：正文以 `对话摘要：` 开头，然后是子弹
    """
    # TODO
    raise NotImplementedError


def compact_exchanges(
    exchanges: Sequence[Exchange],
    *,
    keep_recent_turns: int,
    previous_summary: str | None = None,
    summarizer: Summarizer | None = None,
    system_prompt: str | None = None,
) -> CompactResult:
    """将过长对话折叠为「摘要 + 最近轮」，不修改入参。

    规则概要：
    1. keep_recent_turns < 1 → ValueError
    2. 轮数 <= keep_recent_turns：不折叠；summary 保持 previous_summary
    3. 否则折叠最旧的 (len - keep_recent_turns) 轮；recent 正好 keep_recent_turns 轮
    4. summarizer 默认 default_summarize；new_summary = summarizer(folded, previous_summary)
    5. messages 顺序：可选 system_prompt → 摘要消息（若有）→ 最近轮 user/assistant
    6. system_prompt 若提供则必须非空 strip，否则 ValueError
    """
    # TODO
    raise NotImplementedError


class SummarizingMemory:
    """带滚动摘要的会话记忆：超出最近轮数时自动折叠。"""

    def __init__(
        self,
        *,
        keep_recent_turns: int = 2,
        system_prompt: str | None = None,
        summarizer: Summarizer | None = None,
    ) -> None:
        # TODO: 校验 keep_recent_turns >= 1；保存 system / summarizer
        raise NotImplementedError

    @property
    def keep_recent_turns(self) -> int:
        # TODO
        raise NotImplementedError

    @property
    def summary(self) -> str | None:
        """当前滚动摘要正文（不含 SUMMARY_MARKER 前缀包装）。"""
        # TODO
        raise NotImplementedError

    def exchanges(self) -> list[Exchange]:
        """当前尚未折叠的最近轮副本。"""
        # TODO
        raise NotImplementedError

    def add_exchange(self, user_text: str, assistant_text: str) -> CompactResult:
        """追加一轮完整对话；若超出 keep_recent_turns 则自动折叠。

        空 user/assistant（strip 后）→ ValueError。
        始终返回 CompactResult（未折叠时 folded 为空列表）。
        """
        # TODO
        raise NotImplementedError

    def context_messages(self) -> list[ChatTurn]:
        """返回当前应发给模型的消息副本。"""
        # TODO
        raise NotImplementedError

    def last_result(self) -> CompactResult | None:
        """最近一次 compact 结果；尚未 add 过则为 None。"""
        # TODO
        raise NotImplementedError

    def reset(self, *, clear_summary: bool = True) -> None:
        """清空最近轮；默认同时清空摘要。"""
        # TODO
        raise NotImplementedError


def build_demo_exchanges() -> list[Exchange]:
    """构造演示用多轮对话。"""
    return [
        ("我叫小前端，请记住。", "好的，小前端。"),
        ("什么是 Agent Loop？", "模型与工具多轮交替直到结束。"),
        ("Guard 是什么？", "工具调用前的硬门禁。"),
        ("HITL 呢？", "危险操作前的人机确认。"),
        ("短记忆和摘要记忆差别？", "短记忆裁窗口；摘要把旧轮压成文字。"),
    ]


def render_summary_report(result: CompactResult) -> str:
    """生成 Markdown 报告，必须包含 REQUIRED_REPORT_SECTIONS 里的二级标题。"""
    # TODO
    raise NotImplementedError
