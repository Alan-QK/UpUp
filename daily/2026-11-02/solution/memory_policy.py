"""Day 64 参考实现：记忆写入策略（何时写入长期记忆）。"""

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

# 显式「请记住」
_EXPLICIT_REMEMBER = re.compile(
    r"(请记住|记住这|帮我记住|别忘了|以后都|下次都|remember\s+(this|that|to)|don't forget)",
    re.IGNORECASE,
)

# 显式「不要记」
_EXPLICIT_FORGET = re.compile(
    r"(不要记住|别记住|忘掉这个|不要存|forget\s+this|do\s+not\s+remember)",
    re.IGNORECASE,
)

# 偏好信号
_PREFERENCE_RE = re.compile(
    r"(我喜欢|我不喜欢|我偏好|我更喜欢|更喜欢|请用.+回答|请用.+写|不要给我|别用|我习惯|优先使用)",
    re.IGNORECASE,
)

# 事实信号
_FACT_RE = re.compile(
    r"(我叫|我的名字是|我是.+工程师|我在.+工作|我的时区|时区是|我住在)",
    re.IGNORECASE,
)

# 寒暄 / 一次性闲聊
_EPHEMERAL_RE = re.compile(
    r"^(你好|您好|嗨|在吗|谢谢|感谢|哈哈|嗯+|好的|ok|okay|早上好|晚安)[\s!！。.~～]*$",
    re.IGNORECASE,
)

# 敏感信息：直接 SKIP，绝不写入
_SENSITIVE_RE = re.compile(
    r"(password|passwd|密码|api[_\s-]?key|secret[_\s-]?key|"
    r"sk-[a-z0-9]{10,}|"
    r"1[3-9]\d{9}|"  # 粗略手机号
    r"\d{17}[\dXx])",  # 粗略身份证
    re.IGNORECASE,
)

# 犹豫语气 → 倾向 ASK
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
    if not isinstance(text, str):
        raise TypeError("text must be str")
    return re.sub(r"\s+", " ", text.strip())


def contains_sensitive(text: str) -> bool:
    """是否命中敏感模式（密码 / Key / 手机号等）。"""
    if not isinstance(text, str):
        raise TypeError("text must be str")
    return bool(_SENSITIVE_RE.search(text))


def _decision(
    text: str,
    *,
    action: str,
    kind: str,
    reason: str,
    confidence: float,
    normalized_text: str,
    role: str,
) -> MemoryDecision:
    return MemoryDecision(
        text=text,
        action=action,
        kind=kind,
        reason=reason,
        confidence=float(confidence),
        normalized_text=normalized_text,
        role=role,
    )


def decide_write(text: str, *, role: str = ROLE_USER) -> MemoryDecision:
    """对单条消息做写入决策（规则启发式，不调用 LLM）。

    决策顺序（从前到后，命中即返回）：
    1. 非 user → SKIP
    2. 空字符串 → SKIP（too_short）
    3. 敏感信息 → SKIP
    4. 显式「不要记」→ SKIP
    5. 显式「请记住」→ WRITE (note/preference，高置信)
    6. 寒暄闲聊 → SKIP
    7. 过短（len < MIN_TEXT_LEN）→ SKIP
    8. 偏好信号 → WRITE 或 ASK（有犹豫词则 ASK）
    9. 事实信号 → WRITE fact
    10. 默认 SKIP
    """
    if not isinstance(text, str):
        raise TypeError("text must be str")
    if role not in VALID_ROLES:
        raise ValueError(f"invalid role: {role}")

    normalized = normalize_candidate(text)

    if role != ROLE_USER:
        return _decision(
            text,
            action=ACTION_SKIP,
            kind=KIND_NONE,
            reason="non_user_role",
            confidence=1.0,
            normalized_text=normalized,
            role=role,
        )

    if not normalized:
        return _decision(
            text,
            action=ACTION_SKIP,
            kind=KIND_NONE,
            reason="too_short",
            confidence=1.0,
            normalized_text=normalized,
            role=role,
        )

    if contains_sensitive(normalized):
        return _decision(
            text,
            action=ACTION_SKIP,
            kind=KIND_NONE,
            reason="sensitive",
            confidence=1.0,
            normalized_text=normalized,
            role=role,
        )

    if _EXPLICIT_FORGET.search(normalized):
        return _decision(
            text,
            action=ACTION_SKIP,
            kind=KIND_NONE,
            reason="explicit_forget",
            confidence=0.95,
            normalized_text=normalized,
            role=role,
        )

    if _EXPLICIT_REMEMBER.search(normalized):
        kind = KIND_PREFERENCE if _PREFERENCE_RE.search(normalized) else KIND_NOTE
        return _decision(
            text,
            action=ACTION_WRITE,
            kind=kind,
            reason="explicit_remember",
            confidence=0.95,
            normalized_text=normalized,
            role=role,
        )

    if _EPHEMERAL_RE.match(normalized):
        return _decision(
            text,
            action=ACTION_SKIP,
            kind=KIND_NONE,
            reason="ephemeral",
            confidence=0.9,
            normalized_text=normalized,
            role=role,
        )

    if len(normalized) < MIN_TEXT_LEN:
        return _decision(
            text,
            action=ACTION_SKIP,
            kind=KIND_NONE,
            reason="too_short",
            confidence=1.0,
            normalized_text=normalized,
            role=role,
        )

    if _PREFERENCE_RE.search(normalized):
        if _HEDGE_RE.search(normalized):
            return _decision(
                text,
                action=ACTION_ASK,
                kind=KIND_PREFERENCE,
                reason="preference_hedged",
                confidence=0.55,
                normalized_text=normalized,
                role=role,
            )
        return _decision(
            text,
            action=ACTION_WRITE,
            kind=KIND_PREFERENCE,
            reason="preference_signal",
            confidence=0.85,
            normalized_text=normalized,
            role=role,
        )

    if _FACT_RE.search(normalized):
        return _decision(
            text,
            action=ACTION_WRITE,
            kind=KIND_FACT,
            reason="fact_signal",
            confidence=0.8,
            normalized_text=normalized,
            role=role,
        )

    return _decision(
        text,
        action=ACTION_SKIP,
        kind=KIND_NONE,
        reason="no_signal",
        confidence=0.7,
        normalized_text=normalized,
        role=role,
    )


def decide_batch(messages: Sequence[tuple[str, str]]) -> list[MemoryDecision]:
    """批量决策。messages: (role, content) 列表。"""
    if not isinstance(messages, (list, tuple)):
        raise TypeError("messages must be sequence")
    out: list[MemoryDecision] = []
    for item in messages:
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError("each message must be (role, content)")
        role, content = item
        out.append(decide_write(content, role=role))
    return out


def filter_writable(decisions: Sequence[MemoryDecision]) -> list[MemoryDecision]:
    """只保留 action=write 的决策（真正可入库）。"""
    return [d for d in decisions if d.action == ACTION_WRITE]


def summarize_decisions(decisions: Sequence[MemoryDecision]) -> PolicyStats:
    """汇总统计。"""
    write_count = skip_count = ask_count = 0
    by_kind: dict[str, int] = {}
    for d in decisions:
        if d.action == ACTION_WRITE:
            write_count += 1
        elif d.action == ACTION_SKIP:
            skip_count += 1
        elif d.action == ACTION_ASK:
            ask_count += 1
        by_kind[d.kind] = by_kind.get(d.kind, 0) + 1
    return PolicyStats(
        total=len(decisions),
        write_count=write_count,
        skip_count=skip_count,
        ask_count=ask_count,
        by_kind=by_kind,
    )


def build_demo_utterances() -> list[tuple[str, str]]:
    """演示用 (role, text) 列表。"""
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
    decisions = decide_batch(build_demo_utterances())
    return decisions, summarize_decisions(decisions)


def render_memory_policy_report(
    decisions: Sequence[MemoryDecision],
    stats: PolicyStats | None = None,
) -> str:
    """生成 Markdown 报告。"""
    stats = stats or summarize_decisions(decisions)
    writable = filter_writable(decisions)
    lines = [
        "# 记忆写入策略报告",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[0]}",
        "",
        "长期记忆不是「每句话都存」。写入策略决定：哪些用户话语值得升级为跨会话条目。",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[1]}",
        "",
        "顺序：角色过滤 → 空串 → 敏感 → 显式勿记 → 显式请记 → 寒暄 → 过短 → 偏好 → 事实 → 默认跳过。",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[2]}",
        "",
        f"- 总条数：{stats.total}",
        f"- WRITE：{stats.write_count}",
        f"- SKIP：{stats.skip_count}",
        f"- ASK：{stats.ask_count}",
        f"- 按 kind：{stats.by_kind}",
        "",
        "可写入样本：",
    ]
    if not writable:
        lines.append("- （无）")
    else:
        for d in writable:
            lines.append(
                f"- [{d.kind}|c={d.confidence:.2f}] {d.normalized_text} （{d.reason}）"
            )
    lines.extend(
        [
            "",
            f"## {REQUIRED_REPORT_SECTIONS[3]}",
            "",
            "WRITE 的条目交给 Day 63 的 VectorMemoryStore.upsert；ASK 走 HITL 确认后再写。",
            "",
            f"## {REQUIRED_REPORT_SECTIONS[4]}",
            "",
            "Day 65：周挑战——带记忆助理，跨两次运行仍记得偏好。",
            "",
        ]
    )
    return "\n".join(lines)
