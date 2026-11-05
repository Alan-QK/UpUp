"""Day 61 参考实现：增强历史窗口（短时会话记忆）。"""

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
    """教学用启发式：空串 0，否则 max(1, (len + 3) // 4)。"""
    if not isinstance(text, str):
        raise TypeError("text must be str")
    if text == "":
        return 0
    return max(1, (len(text) + 3) // 4)


def message_tokens(msg: ChatTurn) -> int:
    """单条消息估 token（content + role 开销 1）。"""
    return estimate_tokens(msg.content) + 1


def count_exchange_turns(messages: Sequence[ChatTurn]) -> int:
    """统计完整 user+assistant 轮数。"""
    return len(_iter_exchange_pairs(messages))


def _iter_exchange_pairs(messages: Sequence[ChatTurn]) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    i = 0
    n = len(messages)
    while i < n:
        if (
            messages[i].role == ROLE_USER
            and i + 1 < n
            and messages[i + 1].role == ROLE_ASSISTANT
        ):
            pairs.append((i, i + 1))
            i += 2
            continue
        i += 1
    return pairs


def apply_enhanced_window(
    messages: Sequence[ChatTurn],
    *,
    max_turns: int | None = None,
    max_tokens: int | None = None,
    keep_system: bool = True,
) -> WindowResult:
    """按保护项 + 轮数 + token 预算裁剪历史，不修改入参。

    规则：
    1. system（若 keep_system）与 pinned 一律保留
    2. 其余只考虑完整 user+assistant 轮；从新到旧选取
    3. max_turns 限制轮数；max_tokens 限制估 token（保护项先占预算）
    4. 两者都给时：先按轮数候选，再按预算从新到旧装入
    5. 非保护的孤立消息（落单 user/tool 等）默认丢弃
    """
    if max_turns is not None and max_turns < 1:
        raise ValueError("max_turns must be >= 1 when provided")
    if max_tokens is not None and max_tokens < 1:
        raise ValueError("max_tokens must be >= 1 when provided")
    if max_turns is None and max_tokens is None:
        raise ValueError("must provide max_turns and/or max_tokens")

    original = list(messages)
    protected: set[int] = set()
    for i, msg in enumerate(original):
        if keep_system and msg.role == ROLE_SYSTEM:
            protected.add(i)
        elif msg.pinned:
            protected.add(i)

    pairs = _iter_exchange_pairs(original)
    # 候选轮：两端索引都不在 protected 里才算「可裁剪轮」
    # 若一轮中有 pinned，整轮因 protected 已留，这里跳过避免重复
    flexible_pairs = [
        (u, a) for (u, a) in pairs if u not in protected and a not in protected
    ]

    if max_turns is not None:
        flexible_pairs = flexible_pairs[-max_turns:]

    selected: set[int] = set(protected)
    used = sum(message_tokens(original[i]) for i in selected)

    if max_tokens is None:
        for u, a in flexible_pairs:
            selected.add(u)
            selected.add(a)
    else:
        for u, a in reversed(flexible_pairs):
            cost = message_tokens(original[u]) + message_tokens(original[a])
            if used + cost <= max_tokens:
                selected.add(u)
                selected.add(a)
                used += cost

    kept = [original[i] for i in range(len(original)) if i in selected]
    dropped = [original[i] for i in range(len(original)) if i not in selected]
    stats = WindowStats(
        input_messages=len(original),
        kept_messages=len(kept),
        dropped_messages=len(dropped),
        estimated_tokens_kept=sum(message_tokens(m) for m in kept),
        estimated_tokens_dropped=sum(message_tokens(m) for m in dropped),
        max_turns=max_turns,
        max_tokens=max_tokens,
        pinned_kept=sum(1 for m in kept if m.pinned),
        system_kept=sum(1 for m in kept if m.role == ROLE_SYSTEM),
    )
    return WindowResult(messages=kept, dropped=dropped, stats=stats)


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
        if max_turns is None and max_tokens is None:
            raise ValueError("must provide max_turns and/or max_tokens")
        if max_turns is not None and max_turns < 1:
            raise ValueError("max_turns must be >= 1 when provided")
        if max_tokens is not None and max_tokens < 1:
            raise ValueError("max_tokens must be >= 1 when provided")
        self._max_turns = max_turns
        self._max_tokens = max_tokens
        self._keep_system = keep_system
        self._messages: list[ChatTurn] = []
        self._last_result: WindowResult | None = None
        if system_prompt is not None:
            prompt = system_prompt.strip()
            if not prompt:
                raise ValueError("empty system_prompt")
            self._messages.append(ChatTurn(role=ROLE_SYSTEM, content=prompt))

    @property
    def max_turns(self) -> int | None:
        return self._max_turns

    @property
    def max_tokens(self) -> int | None:
        return self._max_tokens

    def add(self, role: str, content: str, *, pinned: bool = False) -> None:
        if role not in VALID_ROLES:
            raise ValueError(f"invalid role: {role}")
        if role in (ROLE_USER, ROLE_SYSTEM) and not content.strip():
            raise ValueError("empty content")
        self._messages.append(ChatTurn(role=role, content=content, pinned=pinned))
        self._reapply()

    def add_exchange(self, user_text: str, assistant_text: str) -> None:
        """追加一轮完整对话并裁剪。"""
        u = user_text.strip()
        a = assistant_text.strip()
        if not u or not a:
            raise ValueError("empty content")
        self._messages.append(ChatTurn(role=ROLE_USER, content=u))
        self._messages.append(ChatTurn(role=ROLE_ASSISTANT, content=a))
        self._reapply()

    def _reapply(self) -> None:
        self._last_result = apply_enhanced_window(
            self._messages,
            max_turns=self._max_turns,
            max_tokens=self._max_tokens,
            keep_system=self._keep_system,
        )
        self._messages = list(self._last_result.messages)

    def history(self) -> list[ChatTurn]:
        return list(self._messages)

    def last_result(self) -> WindowResult | None:
        return self._last_result

    def reset(self, *, keep_system_messages: bool = True) -> None:
        if keep_system_messages:
            self._messages = [m for m in self._messages if m.role == ROLE_SYSTEM]
        else:
            self._messages.clear()
        self._last_result = None


def build_demo_transcript() -> list[ChatTurn]:
    """构造一段可演示的多轮对话（含一条 pinned 偏好）。"""
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
    """生成含固定二级标题的 Markdown 报告。"""
    s = result.stats
    lines = [
        "# 短时会话记忆 · 窗口报告",
        "",
        "## 何为短记忆",
        "",
        "短时会话记忆是当前请求里模型能看见的 messages；裁剪策略决定它还记不记得旧事实。",
        "",
        "## 增强策略",
        "",
        f"- max_turns: `{s.max_turns}`",
        f"- max_tokens: `{s.max_tokens}`",
        "- 保护：system（可配）+ pinned",
        "- 观察：dropped 列表解释「突然遗忘」",
        "",
        "## 与 Day16 对比",
        "",
        "Day16 只按轮滑动；今天叠加 token 预算、钉住与统计，便于挂到 Agent Loop 前。",
        "",
        "## 今日演示统计",
        "",
        f"- input: {s.input_messages}",
        f"- kept: {s.kept_messages}（tokens≈{s.estimated_tokens_kept}）",
        f"- dropped: {s.dropped_messages}（tokens≈{s.estimated_tokens_dropped}）",
        f"- system_kept: {s.system_kept} · pinned_kept: {s.pinned_kept}",
        "",
        "保留消息：",
    ]
    for m in result.messages:
        pin = " 📌" if m.pinned else ""
        lines.append(f"- [{m.role}]{pin} {m.content}")
    lines.append("")
    lines.append("丢弃消息：")
    if not result.dropped:
        lines.append("- （无）")
    else:
        for m in result.dropped:
            lines.append(f"- [{m.role}] {m.content}")
    lines.extend(
        [
            "",
            "## 明日预告",
            "",
            "Day 62 将把窗口外旧轮压成摘要记忆，而不是直接丢掉。",
            "",
        ]
    )
    text = "\n".join(lines)
    for section in REQUIRED_REPORT_SECTIONS:
        if f"## {section}" not in text:
            raise RuntimeError(f"missing section: {section}")
    return text
