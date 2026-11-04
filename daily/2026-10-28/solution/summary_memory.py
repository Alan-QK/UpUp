"""Day 62 参考实现：摘要记忆（超长对话自动折叠）。"""

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
    """教学用启发式：空串 0，否则 max(1, (len + 3) // 4)。"""
    if not isinstance(text, str):
        raise TypeError("text must be str")
    if text == "":
        return 0
    return max(1, (len(text) + 3) // 4)


def format_summary_message(summary: str) -> ChatTurn:
    """把摘要包装成带标记的 system 消息。"""
    if not isinstance(summary, str):
        raise TypeError("summary must be str")
    body = summary.strip()
    if not body:
        raise ValueError("empty summary")
    if body.startswith(SUMMARY_MARKER):
        content = body
    else:
        content = f"{SUMMARY_MARKER}\n{body}"
    return ChatTurn(role=ROLE_SYSTEM, content=content)


def is_summary_message(msg: ChatTurn) -> bool:
    """判断是否为摘要 system 消息。"""
    return msg.role == ROLE_SYSTEM and msg.content.startswith(SUMMARY_MARKER)


def _clip(text: str, limit: int = 40) -> str:
    one_line = text.strip().replace("\n", " ")
    if len(one_line) <= limit:
        return one_line
    return one_line[: limit - 3] + "..."


def default_summarize(
    exchanges: Sequence[Exchange],
    previous_summary: str | None = None,
) -> str:
    """确定性 mock 摘要器。"""
    if not exchanges:
        raise ValueError("exchanges must not be empty")
    bullets: list[str] = []
    for user_text, assistant_text in exchanges:
        bullets.append(
            f"- 用户：{_clip(user_text)} → 助手：{_clip(assistant_text)}"
        )
    prev = (previous_summary or "").strip()
    if prev:
        return "\n".join([prev, "近期折叠：", *bullets])
    return "\n".join(["对话摘要：", *bullets])


def _build_messages(
    *,
    system_prompt: str | None,
    summary_text: str | None,
    recent: Sequence[Exchange],
) -> list[ChatTurn]:
    messages: list[ChatTurn] = []
    if system_prompt is not None:
        messages.append(ChatTurn(role=ROLE_SYSTEM, content=system_prompt))
    if summary_text:
        messages.append(format_summary_message(summary_text))
    for user_text, assistant_text in recent:
        messages.append(ChatTurn(role=ROLE_USER, content=user_text))
        messages.append(ChatTurn(role=ROLE_ASSISTANT, content=assistant_text))
    return messages


def _context_tokens(messages: Sequence[ChatTurn]) -> int:
    return sum(estimate_tokens(m.content) + 1 for m in messages)


def compact_exchanges(
    exchanges: Sequence[Exchange],
    *,
    keep_recent_turns: int,
    previous_summary: str | None = None,
    summarizer: Summarizer | None = None,
    system_prompt: str | None = None,
) -> CompactResult:
    """将过长对话折叠为「摘要 + 最近轮」，不修改入参。"""
    if keep_recent_turns < 1:
        raise ValueError("keep_recent_turns must be >= 1")

    prompt: str | None = None
    if system_prompt is not None:
        prompt = system_prompt.strip()
        if not prompt:
            raise ValueError("empty system_prompt")

    original = [(u, a) for u, a in exchanges]
    fn = summarizer or default_summarize

    if len(original) <= keep_recent_turns:
        folded: list[Exchange] = []
        recent = original
        summary_text = previous_summary
    else:
        fold_n = len(original) - keep_recent_turns
        folded = original[:fold_n]
        recent = original[fold_n:]
        summary_text = fn(folded, previous_summary)

    messages = _build_messages(
        system_prompt=prompt,
        summary_text=summary_text,
        recent=recent,
    )
    summary_chars = len(summary_text) if summary_text else 0
    stats = CompactStats(
        input_exchanges=len(original),
        kept_recent_exchanges=len(recent),
        folded_exchanges=len(folded),
        summary_chars=summary_chars,
        estimated_tokens_context=_context_tokens(messages),
        keep_recent_turns=keep_recent_turns,
    )
    return CompactResult(
        messages=messages,
        folded=list(folded),
        summary_text=summary_text,
        stats=stats,
    )


class SummarizingMemory:
    """带滚动摘要的会话记忆：超出最近轮数时自动折叠。"""

    def __init__(
        self,
        *,
        keep_recent_turns: int = 2,
        system_prompt: str | None = None,
        summarizer: Summarizer | None = None,
    ) -> None:
        if keep_recent_turns < 1:
            raise ValueError("keep_recent_turns must be >= 1")
        prompt: str | None = None
        if system_prompt is not None:
            prompt = system_prompt.strip()
            if not prompt:
                raise ValueError("empty system_prompt")
        self._keep_recent_turns = keep_recent_turns
        self._system_prompt = prompt
        self._summarizer = summarizer or default_summarize
        self._exchanges: list[Exchange] = []
        self._summary: str | None = None
        self._last_result: CompactResult | None = None

    @property
    def keep_recent_turns(self) -> int:
        return self._keep_recent_turns

    @property
    def summary(self) -> str | None:
        return self._summary

    def exchanges(self) -> list[Exchange]:
        return list(self._exchanges)

    def add_exchange(self, user_text: str, assistant_text: str) -> CompactResult:
        user = user_text.strip()
        assistant = assistant_text.strip()
        if not user or not assistant:
            raise ValueError("empty content")
        self._exchanges.append((user, assistant))
        result = compact_exchanges(
            self._exchanges,
            keep_recent_turns=self._keep_recent_turns,
            previous_summary=self._summary,
            summarizer=self._summarizer,
            system_prompt=self._system_prompt,
        )
        # 折叠后只保留消息里的最近 user/assistant 对，并更新滚动摘要
        recent_msgs = [
            m for m in result.messages if m.role in (ROLE_USER, ROLE_ASSISTANT)
        ]
        rebuilt: list[Exchange] = []
        i = 0
        while i + 1 < len(recent_msgs):
            if (
                recent_msgs[i].role == ROLE_USER
                and recent_msgs[i + 1].role == ROLE_ASSISTANT
            ):
                rebuilt.append(
                    (recent_msgs[i].content, recent_msgs[i + 1].content)
                )
                i += 2
            else:
                i += 1
        self._exchanges = rebuilt
        self._summary = result.summary_text
        self._last_result = result
        return result

    def context_messages(self) -> list[ChatTurn]:
        result = compact_exchanges(
            self._exchanges,
            keep_recent_turns=self._keep_recent_turns,
            previous_summary=self._summary,
            summarizer=self._summarizer,
            system_prompt=self._system_prompt,
        )
        return list(result.messages)

    def last_result(self) -> CompactResult | None:
        return self._last_result

    def reset(self, *, clear_summary: bool = True) -> None:
        self._exchanges.clear()
        if clear_summary:
            self._summary = None
        self._last_result = None


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
    """生成含固定二级标题的 Markdown 报告。"""
    s = result.stats
    lines = [
        "# 摘要记忆 · 压缩报告",
        "",
        "## 何为摘要记忆",
        "",
        "摘要记忆把窗口外的旧轮压成一段文字继续挂在上下文里，用有损压缩换 token。",
        "",
        "## 滚动合并策略",
        "",
        f"- keep_recent_turns: `{s.keep_recent_turns}`",
        f"- 本次折叠轮数: {s.folded_exchanges}",
        f"- 摘要字符数: {s.summary_chars}",
        "- 新旧摘要合并：`summarize(刚折叠的轮, previous_summary)`",
        "",
        "## 与短窗口对比",
        "",
        "短窗口（Day 61）直接丢掉旧轮；摘要记忆把旧轮压缩后挂回，细节可能丢但线索还在。",
        "",
        "## 今日演示统计",
        "",
        f"- input_exchanges: {s.input_exchanges}",
        f"- kept_recent: {s.kept_recent_exchanges}",
        f"- folded: {s.folded_exchanges}",
        f"- context tokens≈{s.estimated_tokens_context}",
        "",
        "摘要正文：",
        "",
        result.summary_text or "（无）",
        "",
        "上下文消息：",
    ]
    for m in result.messages:
        marker = " 📝" if is_summary_message(m) else ""
        lines.append(f"- [{m.role}]{marker} {m.content}")
    lines.extend(
        [
            "",
            "## 明日预告",
            "",
            "Day 63 将做长期向量记忆：跨会话存储与检索用户偏好。",
            "",
        ]
    )
    text = "\n".join(lines)
    for section in REQUIRED_REPORT_SECTIONS:
        if f"## {section}" not in text:
            raise RuntimeError(f"missing section: {section}")
    return text
