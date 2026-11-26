"""Day 65 参考实现：带记忆助理（跨两次运行仍记得偏好）。

综合 Day 61–64：
- 写入闸门（write / skip / ask）
- mock 向量检索
- JSON 文件持久化（进程退出后仍在）
- 第二次运行加载同一文件即可召回偏好
"""

from __future__ import annotations

import json
import math
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

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

ConfirmFn = Callable[[str, str], bool]  # (text, reason) -> 是否写入
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


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------


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
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence out of range")


@dataclass(frozen=True)
class MemoryItem:
    """一条可持久化的长期记忆。"""

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
    """一轮对话的结果。"""

    user_text: str
    reply: str
    decision: MemoryDecision
    recalled: list[ScoredMemory]
    wrote: MemoryItem | None
    context_block: str | None


@dataclass(frozen=True)
class SessionStats:
    """一次会话（可跨运行）的统计。"""

    user_id: str
    turns: int
    write_count: int
    skip_count: int
    ask_count: int
    ask_accepted: int
    store_size: int
    store_path: str


# ---------------------------------------------------------------------------
# 写入策略（Day 64 精简复用）
# ---------------------------------------------------------------------------


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
    """写入闸门：与 Day 64 同序，命中即返回。"""
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


# ---------------------------------------------------------------------------
# Embedding + 相似度（Day 63）
# ---------------------------------------------------------------------------


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
    """确定性教学 embedding：勿用内置 hash()。"""
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


# ---------------------------------------------------------------------------
# 文件持久化向量库
# ---------------------------------------------------------------------------


class FileMemoryStore:
    """JSON 文件持久化的向量记忆库：跨进程 / 跨运行可加载。"""

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
        if self.path.exists():
            self.load()

    def size(self, user_id: str | None = None) -> int:
        if user_id is None:
            return len(self._items)
        uid = user_id.strip()
        return sum(1 for it in self._items.values() if it.user_id == uid)

    def list_user(self, user_id: str) -> list[MemoryItem]:
        uid = user_id.strip()
        if not uid:
            raise ValueError("empty user_id")
        return [it for it in self._items.values() if it.user_id == uid]

    def upsert(
        self,
        *,
        user_id: str,
        text: str,
        kind: str = KIND_PREFERENCE,
        memory_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> MemoryItem:
        uid = user_id.strip()
        body = text.strip()
        if not uid:
            raise ValueError("empty user_id")
        if not body:
            raise ValueError("empty text")
        if kind not in PERSIST_KINDS:
            raise ValueError(f"invalid kind: {kind}")
        mid = (memory_id or "").strip() or f"mem-{uuid.uuid4().hex[:12]}"
        emb = self._embed(body)
        if len(emb) != EMBED_DIM:
            raise ValueError("embedding dim mismatch")
        item = MemoryItem(
            id=mid,
            user_id=uid,
            text=body,
            kind=kind,
            embedding=tuple(float(x) for x in emb),
            metadata=dict(metadata or {}),
        )
        self._items[mid] = item
        if self.autosave:
            self.save()
        return item

    def search(
        self,
        query: str,
        *,
        user_id: str,
        top_k: int = 3,
        min_score: float = 0.15,
    ) -> list[ScoredMemory]:
        q = query.strip()
        uid = user_id.strip()
        if not q:
            raise ValueError("empty query")
        if not uid:
            raise ValueError("empty user_id")
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        q_emb = self._embed(q)
        scored: list[ScoredMemory] = []
        for item in self._items.values():
            if item.user_id != uid:
                continue
            score = cosine_similarity(q_emb, item.embedding)
            if score >= min_score:
                scored.append(ScoredMemory(item=item, score=score))
        scored.sort(key=lambda s: (-s.score, s.item.id))
        return scored[:top_k]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": STORE_VERSION,
            "items": [it.to_dict() for it in self._items.values()],
        }
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def load(self) -> int:
        if not self.path.exists():
            self._items.clear()
            return 0
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("invalid store format")
        items_raw = raw.get("items") or []
        if not isinstance(items_raw, list):
            raise ValueError("invalid items")
        loaded: dict[str, MemoryItem] = {}
        for row in items_raw:
            item = MemoryItem.from_dict(row)
            loaded[item.id] = item
        self._items = loaded
        return len(loaded)

    def clear(self, user_id: str | None = None) -> int:
        if user_id is None:
            n = len(self._items)
            self._items.clear()
        else:
            uid = user_id.strip()
            if not uid:
                raise ValueError("empty user_id")
            to_del = [k for k, v in self._items.items() if v.user_id == uid]
            for k in to_del:
                del self._items[k]
            n = len(to_del)
        if self.autosave:
            self.save()
        return n


# ---------------------------------------------------------------------------
# 助理：召回 → 回复 → 决策 → 写入 → 落盘
# ---------------------------------------------------------------------------


def default_confirm(_text: str, _reason: str) -> bool:
    """默认对 ASK 拒绝写入（保守）；测试可注入 True。"""
    return False


def build_mock_reply(user_text: str, recalled: Sequence[ScoredMemory]) -> str:
    """无 LLM：根据召回记忆拼一句可验证的回复。"""
    if not recalled:
        return f"收到：{normalize_candidate(user_text)}。我还没有关于你的长期记忆。"
    prefs = [s.item.text for s in recalled]
    joined = "；".join(prefs)
    return (
        f"收到：{normalize_candidate(user_text)}。"
        f"根据我记得的偏好：{joined}。"
    )


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
        uid = user_id.strip()
        if not uid:
            raise ValueError("empty user_id")
        self.user_id = uid
        self.store = FileMemoryStore(store_path)
        self.confirm_fn = confirm_fn or default_confirm
        self.top_k = top_k
        self.min_score = min_score
        self._turns = 0
        self._write_count = 0
        self._skip_count = 0
        self._ask_count = 0
        self._ask_accepted = 0

    def handle_turn(self, user_text: str) -> TurnResult:
        if not isinstance(user_text, str):
            raise TypeError("user_text must be str")

        recalled = self.store.search(
            user_text,
            user_id=self.user_id,
            top_k=self.top_k,
            min_score=self.min_score,
        )
        context_block = format_memory_block(recalled)
        reply = build_mock_reply(user_text, recalled)
        decision = decide_write(user_text, role=ROLE_USER)

        wrote: MemoryItem | None = None
        if decision.action == ACTION_WRITE:
            wrote = self.store.upsert(
                user_id=self.user_id,
                text=decision.normalized_text,
                kind=decision.kind if decision.kind in PERSIST_KINDS else KIND_NOTE,
                metadata={"reason": decision.reason},
            )
            self._write_count += 1
        elif decision.action == ACTION_ASK:
            self._ask_count += 1
            if self.confirm_fn(decision.normalized_text, decision.reason):
                wrote = self.store.upsert(
                    user_id=self.user_id,
                    text=decision.normalized_text,
                    kind=KIND_PREFERENCE,
                    metadata={"reason": decision.reason, "via": "ask"},
                )
                self._ask_accepted += 1
                self._write_count += 1
            else:
                self._skip_count += 1
        else:
            self._skip_count += 1

        self._turns += 1
        return TurnResult(
            user_text=user_text,
            reply=reply,
            decision=decision,
            recalled=list(recalled),
            wrote=wrote,
            context_block=context_block,
        )

    def stats(self) -> SessionStats:
        return SessionStats(
            user_id=self.user_id,
            turns=self._turns,
            write_count=self._write_count,
            skip_count=self._skip_count,
            ask_count=self._ask_count,
            ask_accepted=self._ask_accepted,
            store_size=self.store.size(self.user_id),
            store_path=str(self.store.path),
        )


# ---------------------------------------------------------------------------
# 跨运行演示 + 报告
# ---------------------------------------------------------------------------


def run_cross_session_demo(store_path: str | Path) -> tuple[list[TurnResult], list[TurnResult], SessionStats]:
    """两次独立 MemoryAssistant 实例，共享同一 JSON 文件。

    会话 1：写入偏好 / 事实，寒暄与敏感应跳过。
    会话 2：新进程语义下重新 load，对「主题 / 语言」类问题应召回偏好。
    """
    path = Path(store_path)
    if path.exists():
        path.unlink()

    # --- 会话 1 ---
    a1 = MemoryAssistant(path, user_id=DEFAULT_USER_ID, confirm_fn=lambda _t, _r: False)
    session1_inputs = [
        "你好",
        "请记住：以后都用中文回答我",
        "我喜欢深色主题，少一点动画",
        "我叫小凯，是一名前端工程师",
        "我的密码是 Secret123",
        "帮我看看这个按钮怎么居中",
    ]
    results1 = [a1.handle_turn(t) for t in session1_inputs]
    stats_mid = a1.stats()

    # --- 会话 2：新实例，同文件 ---
    a2 = MemoryAssistant(path, user_id=DEFAULT_USER_ID)
    session2_inputs = [
        "我想换个界面主题，你有什么建议？",
        "回答请用什么语言比较好？",
    ]
    results2 = [a2.handle_turn(t) for t in session2_inputs]

    # 合并统计：会话2 的 store_size 才是最终
    final = SessionStats(
        user_id=DEFAULT_USER_ID,
        turns=stats_mid.turns + a2.stats().turns,
        write_count=stats_mid.write_count + a2.stats().write_count,
        skip_count=stats_mid.skip_count + a2.stats().skip_count,
        ask_count=stats_mid.ask_count + a2.stats().ask_count,
        ask_accepted=stats_mid.ask_accepted + a2.stats().ask_accepted,
        store_size=a2.stats().store_size,
        store_path=str(path),
    )
    return results1, results2, final


def render_memory_assistant_report(
    results1: Sequence[TurnResult],
    results2: Sequence[TurnResult],
    stats: SessionStats,
) -> str:
    """生成含固定二级标题的 Markdown 报告。"""
    lines = [
        "# 带记忆助理 · 周挑战报告",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[0]}",
        "",
        "带记忆助理 = 对话回合 + 写入闸门 + 向量召回 + **磁盘持久化**。"
        "关掉进程再打开，仍能按 user_id 想起偏好——这才叫跨会话记忆。",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[1]}",
        "",
        "- Day 61 短记忆：窗口（本挑战用单轮召回代替，聚焦长期）",
        "- Day 62 摘要：有损压缩（本挑战未强制，可后续挂上）",
        "- Day 63 向量记忆：mock_embed + 余弦检索",
        "- Day 64 写入策略：write / skip / ask",
        "- **今天**：FileMemoryStore 把条目落到 JSON，第二次 `MemoryAssistant` 直接 load",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[2]}",
        "",
        "### 会话 1（写入）",
        "",
    ]
    for r in results1:
        wrote = r.wrote.text if r.wrote else "—"
        lines.append(
            f"- user: {normalize_candidate(r.user_text)} → [{r.decision.action}] "
            f"reason={r.decision.reason} wrote={wrote}"
        )
    lines.extend(["", "### 会话 2（召回）", ""])
    for r in results2:
        n_hit = len(r.recalled)
        lines.append(f"- Q: {normalize_candidate(r.user_text)}")
        lines.append(f"  - hits={n_hit}")
        lines.append(f"  - reply: {r.reply}")
    lines.extend(
        [
            "",
            f"## {REQUIRED_REPORT_SECTIONS[3]}",
            "",
            f"- user_id: `{stats.user_id}`",
            f"- turns: {stats.turns}",
            f"- write / skip / ask: {stats.write_count} / {stats.skip_count} / {stats.ask_count}",
            f"- ask_accepted: {stats.ask_accepted}",
            f"- store_size: {stats.store_size}",
            f"- store_path: `{stats.store_path}`",
            "",
            f"## {REQUIRED_REPORT_SECTIONS[4]}",
            "",
            "Week 14 起做任务分解与 Plan-and-Execute：Day 66 Planner。",
            "",
        ]
    )
    text = "\n".join(lines)
    for section in REQUIRED_REPORT_SECTIONS:
        if f"## {section}" not in text:
            raise RuntimeError(f"missing section: {section}")
    return text
