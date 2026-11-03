"""Day 65 练习：带记忆助理（跨两次运行仍记得偏好）。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——不调用 LLM，不接真实向量数据库。

本周拼装：
- Day 64 写入闸门（decide_write 已给齐）
- Day 63 mock_embed / 余弦检索（已给齐）
- 今天重点：FileMemoryStore 持久化 + MemoryAssistant 跨运行召回
"""

from __future__ import annotations

import json
import math
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

EMBED_DIM = 32
MEMORY_MARKER = "[长期记忆]"

ACTION_WRITE = "write"
ACTION_SKIP = "skip"
ACTION_ASK = "ask"
VALID_ACTIONS = frozenset({ACTION_WRITE, ACTION_SKIP, ACTION_ASK})

KIND_PREFERENCE = "preference"
KIND_FACT = "fact"
KIND_NOTE = "note"
KIND_NONE = "none"
VALID_KINDS = frozenset({KIND_PREFERENCE, KIND_FACT, KIND_NOTE, KIND_NONE})
PERSIST_KINDS = frozenset({KIND_PREFERENCE, KIND_FACT, KIND_NOTE})

ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_SYSTEM = "system"
VALID_ROLES = frozenset({ROLE_USER, ROLE_ASSISTANT, ROLE_SYSTEM})

MIN_TEXT_LEN = 2
DEFAULT_USER_ID = "u-demo"
STORE_VERSION = 1

REQUIRED_REPORT_SECTIONS = (
    "何为带记忆助理",
    "本周能力拼装",
    "跨运行演示",
    "今日演示统计",
    "下周预告",
)

ConfirmFn = Callable[[str, str], bool]
EmbedFn = Callable[[str], list[float]]

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
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence out of range")


@dataclass(frozen=True)
class MemoryItem:
    id: str
    user_id: str
    text: str
    kind: str
    embedding: tuple[float, ...]
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("empty id")
        if not self.user_id.strip():
            raise ValueError("empty user_id")
        if not self.text.strip():
            raise ValueError("empty text")
        if self.kind not in PERSIST_KINDS:
            raise ValueError(f"invalid kind: {self.kind}")
        if len(self.embedding) != EMBED_DIM:
            raise ValueError("embedding dim mismatch")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "text": self.text,
            "kind": self.kind,
            "embedding": list(self.embedding),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict) -> MemoryItem:
        return cls(
            id=str(data["id"]),
            user_id=str(data["user_id"]),
            text=str(data["text"]),
            kind=str(data["kind"]),
            embedding=tuple(float(x) for x in data["embedding"]),
            metadata={str(k): str(v) for k, v in dict(data.get("metadata") or {}).items()},
        )


@dataclass(frozen=True)
class ScoredMemory:
    item: MemoryItem
    score: float


@dataclass(frozen=True)
class TurnResult:
    user_text: str
    reply: str
    decision: MemoryDecision
    recalled: list[ScoredMemory]
    wrote: MemoryItem | None
    context_block: str | None


@dataclass(frozen=True)
class SessionStats:
    user_id: str
    turns: int
    write_count: int
    skip_count: int
    ask_count: int
    ask_accepted: int
    store_size: int
    store_path: str


# ----- 写入策略（已给齐，勿改语义）-----


def normalize_candidate(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be str")
    return re.sub(r"\s+", " ", text.strip())


def contains_sensitive(text: str) -> bool:
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
    """与 Day 64 同序。已实现，可直接调用。"""
    if not isinstance(text, str):
        raise TypeError("text must be str")
    if role not in VALID_ROLES:
        raise ValueError(f"invalid role: {role}")

    normalized = normalize_candidate(text)

    if role != ROLE_USER:
        return _decision(
            text, action=ACTION_SKIP, kind=KIND_NONE, reason="non_user_role",
            confidence=1.0, normalized_text=normalized, role=role,
        )
    if not normalized:
        return _decision(
            text, action=ACTION_SKIP, kind=KIND_NONE, reason="too_short",
            confidence=1.0, normalized_text=normalized, role=role,
        )
    if contains_sensitive(normalized):
        return _decision(
            text, action=ACTION_SKIP, kind=KIND_NONE, reason="sensitive",
            confidence=1.0, normalized_text=normalized, role=role,
        )
    if _EXPLICIT_FORGET.search(normalized):
        return _decision(
            text, action=ACTION_SKIP, kind=KIND_NONE, reason="explicit_forget",
            confidence=0.95, normalized_text=normalized, role=role,
        )
    if _EXPLICIT_REMEMBER.search(normalized):
        kind = KIND_PREFERENCE if _PREFERENCE_RE.search(normalized) else KIND_NOTE
        return _decision(
            text, action=ACTION_WRITE, kind=kind, reason="explicit_remember",
            confidence=0.95, normalized_text=normalized, role=role,
        )
    if _EPHEMERAL_RE.match(normalized):
        return _decision(
            text, action=ACTION_SKIP, kind=KIND_NONE, reason="ephemeral",
            confidence=0.9, normalized_text=normalized, role=role,
        )
    if len(normalized) < MIN_TEXT_LEN:
        return _decision(
            text, action=ACTION_SKIP, kind=KIND_NONE, reason="too_short",
            confidence=1.0, normalized_text=normalized, role=role,
        )
    if _PREFERENCE_RE.search(normalized):
        if _HEDGE_RE.search(normalized):
            return _decision(
                text, action=ACTION_ASK, kind=KIND_PREFERENCE, reason="preference_hedged",
                confidence=0.55, normalized_text=normalized, role=role,
            )
        return _decision(
            text, action=ACTION_WRITE, kind=KIND_PREFERENCE, reason="preference_signal",
            confidence=0.85, normalized_text=normalized, role=role,
        )
    if _FACT_RE.search(normalized):
        return _decision(
            text, action=ACTION_WRITE, kind=KIND_FACT, reason="fact_signal",
            confidence=0.8, normalized_text=normalized, role=role,
        )
    return _decision(
        text, action=ACTION_SKIP, kind=KIND_NONE, reason="no_signal",
        confidence=0.7, normalized_text=normalized, role=role,
    )


# ----- Embedding（已给齐）-----


def _stable_bucket(token: str, dim: int = EMBED_DIM) -> int:
    h = 2166136261
    for b in token.encode("utf-8"):
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return h % dim


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return list(vec)
    return [x / norm for x in vec]


def mock_embed(text: str) -> list[float]:
    if not isinstance(text, str):
        raise TypeError("text must be str")
    raw = text.strip().lower()
    vec = [0.0] * EMBED_DIM
    if not raw:
        return vec
    for i, ch in enumerate(raw):
        vec[_stable_bucket(ch)] += 1.0
        if i + 1 < len(raw):
            vec[_stable_bucket(raw[i : i + 2])] += 1.5
    return _l2_normalize(vec)


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not isinstance(a, (list, tuple)) or not isinstance(b, (list, tuple)):
        raise TypeError("vectors must be list or tuple")
    if len(a) == 0 or len(a) != len(b):
        raise ValueError("vector length mismatch")
    dot = norm_a = norm_b = 0.0
    for x, y in zip(a, b):
        fx, fy = float(x), float(y)
        dot += fx * fy
        norm_a += fx * fx
        norm_b += fy * fy
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


def format_memory_block(hits: Sequence[ScoredMemory]) -> str | None:
    if not hits:
        return None
    lines = [MEMORY_MARKER]
    for scored in hits:
        item = scored.item
        lines.append(f"- ({item.kind}, score={scored.score:.3f}) {item.text}")
    return "\n".join(lines)


# ----- 你要完成的部分 -----


class FileMemoryStore:
    """JSON 文件持久化的向量记忆库。"""

    def __init__(
        self,
        path: str | Path,
        *,
        embed_fn: EmbedFn | None = None,
        autosave: bool = True,
    ) -> None:
        self.path = Path(path)
        self._embed = embed_fn or mock_embed
        self.autosave = autosave
        self._items: dict[str, MemoryItem] = {}
        # TODO: 若 path 已存在，调用 self.load()
        raise NotImplementedError("TODO: FileMemoryStore.__init__")

    def size(self, user_id: str | None = None) -> int:
        # TODO: user_id is None → 全库；否则只计该用户
        raise NotImplementedError("TODO: size")

    def list_user(self, user_id: str) -> list[MemoryItem]:
        # TODO: 空 user_id 抛 ValueError；返回该用户全部条目
        raise NotImplementedError("TODO: list_user")

    def upsert(
        self,
        *,
        user_id: str,
        text: str,
        kind: str = KIND_PREFERENCE,
        memory_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> MemoryItem:
        # TODO:
        # 1. 校验 user_id / text / kind
        # 2. 生成 id（或用传入 memory_id）
        # 3. embed → MemoryItem → 写入 self._items
        # 4. autosave 时调用 save()
        raise NotImplementedError("TODO: upsert")

    def search(
        self,
        query: str,
        *,
        user_id: str,
        top_k: int = 3,
        min_score: float = 0.15,
    ) -> list[ScoredMemory]:
        # TODO: 仅在该 user_id 下检索；按分数降序取 top_k；过滤 < min_score
        raise NotImplementedError("TODO: search")

    def save(self) -> None:
        # TODO: 写成 {"version": STORE_VERSION, "items": [...]}
        # 建议先写 .tmp 再 replace，避免半截文件
        raise NotImplementedError("TODO: save")

    def load(self) -> int:
        # TODO: 读 JSON → MemoryItem.from_dict；文件不存在则清空并返回 0
        raise NotImplementedError("TODO: load")

    def clear(self, user_id: str | None = None) -> int:
        # TODO: 清空全部或某用户；autosave 时落盘；返回删除条数
        raise NotImplementedError("TODO: clear")


def default_confirm(_text: str, _reason: str) -> bool:
    """默认对 ASK 拒绝写入（保守）。"""
    return False


def build_mock_reply(user_text: str, recalled: Sequence[ScoredMemory]) -> str:
    """无 LLM：有召回则拼进回复，否则声明尚无长期记忆。"""
    # TODO:
    # - 无召回：f"收到：{normalize_candidate(user_text)}。我还没有关于你的长期记忆。"
    # - 有召回：把各 item.text 用「；」拼接，形如
    #   f"收到：...。根据我记得的偏好：{joined}。"
    raise NotImplementedError("TODO: build_mock_reply")


class MemoryAssistant:
    """带长期记忆的个人助理：同一 store_path 下跨运行可召回。"""

    def __init__(
        self,
        store_path: str | Path,
        *,
        user_id: str = DEFAULT_USER_ID,
        confirm_fn: ConfirmFn | None = None,
        top_k: int = 3,
        min_score: float = 0.15,
    ) -> None:
        # TODO: 校验 user_id；创建 FileMemoryStore；保存 confirm_fn / top_k / min_score
        # 并初始化回合计数器（turns / write / skip / ask / ask_accepted）
        raise NotImplementedError("TODO: MemoryAssistant.__init__")

    def handle_turn(self, user_text: str) -> TurnResult:
        # TODO 流水线：
        # 1. store.search(user_text, user_id=...)
        # 2. format_memory_block + build_mock_reply
        # 3. decide_write(user_text)
        # 4. WRITE → upsert；ASK → confirm_fn 为真才 upsert；否则记 skip
        # 5. 更新计数，返回 TurnResult
        raise NotImplementedError("TODO: handle_turn")

    def stats(self) -> SessionStats:
        # TODO: 组装 SessionStats（store_size 用当前 user 的 size）
        raise NotImplementedError("TODO: stats")


def run_cross_session_demo(store_path: str | Path) -> tuple[list[TurnResult], list[TurnResult], SessionStats]:
    """两次独立 MemoryAssistant，共享同一 JSON 文件。

    会话 1 输入（顺序固定）：
      你好 / 请记住：以后都用中文回答我 / 我喜欢深色主题，少一点动画 /
      我叫小凯，是一名前端工程师 / 我的密码是 Secret123 / 帮我看看这个按钮怎么居中

    会话 2 输入：
      我想换个界面主题，你有什么建议？ /
      回答请用什么语言比较好？

    若 store_path 已存在先删除。confirm_fn 会话 1 用 lambda 拒绝 ASK。
    最终 SessionStats 的 turns/write/skip/ask 为两会话合计，store_size 取会话 2。
    """
    raise NotImplementedError("TODO: run_cross_session_demo")


def render_memory_assistant_report(
    results1: Sequence[TurnResult],
    results2: Sequence[TurnResult],
    stats: SessionStats,
) -> str:
    """生成含 REQUIRED_REPORT_SECTIONS 五个二级标题的 Markdown 报告。"""
    raise NotImplementedError("TODO: render_memory_assistant_report")
