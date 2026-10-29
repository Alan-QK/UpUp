"""Day 63 参考实现：长期向量记忆（跨会话用户偏好）。"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Callable, Sequence

EMBED_DIM = 32
MEMORY_MARKER = "[长期记忆]"
KIND_PREFERENCE = "preference"
KIND_FACT = "fact"
KIND_NOTE = "note"
VALID_KINDS = frozenset({KIND_PREFERENCE, KIND_FACT, KIND_NOTE})

REQUIRED_REPORT_SECTIONS = (
    "何为长期向量记忆",
    "与短记忆/摘要对比",
    "偏好存储与检索",
    "今日演示统计",
    "明日预告",
)

EmbedFn = Callable[[str], list[float]]


@dataclass(frozen=True)
class MemoryItem:
    """一条长期记忆。"""

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
        if self.kind not in VALID_KINDS:
            raise ValueError(f"invalid kind: {self.kind}")
        if len(self.embedding) != EMBED_DIM:
            raise ValueError("embedding dim mismatch")


@dataclass(frozen=True)
class ScoredMemory:
    """带相似度分数的检索结果。"""

    item: MemoryItem
    score: float


@dataclass(frozen=True)
class RecallStats:
    """一次召回的统计。"""

    user_id: str
    query: str
    store_size: int
    candidate_count: int
    returned: int
    top_score: float
    min_score: float
    top_k: int


@dataclass(frozen=True)
class RecallResult:
    """召回结果 + 可注入上下文的文本。"""

    hits: list[ScoredMemory]
    context_block: str | None
    stats: RecallStats


def _stable_bucket(token: str, dim: int = EMBED_DIM) -> int:
    """与 PYTHONHASHSEED 无关的稳定分桶。"""
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
    """确定性教学用 embedding：字符 unigram + bigram 哈希到固定维，再 L2 归一化。"""
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
    """余弦相似度；零向量或长度不一致时按规则处理。"""
    if not isinstance(a, (list, tuple)) or not isinstance(b, (list, tuple)):
        raise TypeError("vectors must be list or tuple")
    if len(a) == 0 or len(a) != len(b):
        raise ValueError("vector length mismatch")
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        fx = float(x)
        fy = float(y)
        dot += fx * fy
        norm_a += fx * fx
        norm_b += fy * fy
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


def format_memory_block(hits: Sequence[ScoredMemory]) -> str | None:
    """把召回结果格式化为可注入 prompt 的文本块；无命中返回 None。"""
    if not hits:
        return None
    lines = [MEMORY_MARKER]
    for scored in hits:
        item = scored.item
        lines.append(
            f"- ({item.kind}, score={scored.score:.3f}) {item.text}"
        )
    return "\n".join(lines)


class VectorMemoryStore:
    """进程内长期向量记忆：按 user_id 隔离，支持偏好写入与语义检索。"""

    def __init__(self, *, embed_fn: EmbedFn | None = None) -> None:
        self._embed = embed_fn or mock_embed
        self._items: dict[str, MemoryItem] = {}

    def size(self, user_id: str | None = None) -> int:
        if user_id is None:
            return len(self._items)
        uid = user_id.strip()
        return sum(1 for it in self._items.values() if it.user_id == uid)

    def get(self, memory_id: str) -> MemoryItem | None:
        return self._items.get(memory_id)

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
        """写入或覆盖一条记忆；embedding 由 embed_fn(text) 生成。"""
        uid = user_id.strip()
        body = text.strip()
        if not uid:
            raise ValueError("empty user_id")
        if not body:
            raise ValueError("empty text")
        if kind not in VALID_KINDS:
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
        return item

    def remember_preference(
        self,
        user_id: str,
        preference: str,
        *,
        memory_id: str | None = None,
    ) -> MemoryItem:
        """语义糖：写入 kind=preference 的记忆。"""
        return self.upsert(
            user_id=user_id,
            text=preference,
            kind=KIND_PREFERENCE,
            memory_id=memory_id,
        )

    def delete(self, memory_id: str) -> bool:
        mid = memory_id.strip()
        if mid in self._items:
            del self._items[mid]
            return True
        return False

    def clear(self, user_id: str | None = None) -> int:
        """清空全部或某用户记忆，返回删除条数。"""
        if user_id is None:
            n = len(self._items)
            self._items.clear()
            return n
        uid = user_id.strip()
        if not uid:
            raise ValueError("empty user_id")
        to_del = [k for k, v in self._items.items() if v.user_id == uid]
        for k in to_del:
            del self._items[k]
        return len(to_del)

    def search(
        self,
        query: str,
        *,
        user_id: str,
        top_k: int = 3,
        min_score: float = 0.15,
    ) -> RecallResult:
        """在指定用户的记忆中做语义检索。"""
        q = query.strip()
        uid = user_id.strip()
        if not q:
            raise ValueError("empty query")
        if not uid:
            raise ValueError("empty user_id")
        if top_k < 1:
            raise ValueError("top_k must be >= 1")

        q_emb = self._embed(q)
        candidates = [it for it in self._items.values() if it.user_id == uid]
        scored: list[ScoredMemory] = []
        for item in candidates:
            score = cosine_similarity(q_emb, item.embedding)
            if score >= min_score:
                scored.append(ScoredMemory(item=item, score=score))
        scored.sort(key=lambda s: (-s.score, s.item.id))
        hits = scored[:top_k]
        top_score = hits[0].score if hits else 0.0
        stats = RecallStats(
            user_id=uid,
            query=q,
            store_size=len(self._items),
            candidate_count=len(candidates),
            returned=len(hits),
            top_score=top_score,
            min_score=min_score,
            top_k=top_k,
        )
        return RecallResult(
            hits=hits,
            context_block=format_memory_block(hits),
            stats=stats,
        )


def build_demo_preferences() -> list[tuple[str, str]]:
    """演示用 (user_id, preference) 列表。"""
    return [
        ("u-front", "我喜欢深色主题，界面尽量少动画"),
        ("u-front", "回答请用中文，代码示例优先 TypeScript"),
        ("u-front", "我在学 Agent，偏好小步可运行练习"),
        ("u-back", "我偏好 Go 语言，不写 Python"),
        ("u-back", "日志用 JSON，不要彩色终端输出"),
    ]


def seed_demo_store(store: VectorMemoryStore | None = None) -> VectorMemoryStore:
    """向 store 写入演示偏好。"""
    target = store or VectorMemoryStore()
    for i, (uid, text) in enumerate(build_demo_preferences(), 1):
        target.remember_preference(uid, text, memory_id=f"demo-{i}")
    return target


def render_vector_memory_report(result: RecallResult) -> str:
    """生成含固定二级标题的 Markdown 报告。"""
    s = result.stats
    lines = [
        "# 长期向量记忆 · 召回报告",
        "",
        "## 何为长期向量记忆",
        "",
        "长期向量记忆把跨会话的偏好/事实写成可检索条目：不塞进每一轮请求，需要时按语义召回。",
        "",
        "## 与短记忆/摘要对比",
        "",
        "- 短记忆（D61）：当前会话窗口，裁剪/pinned",
        "- 摘要记忆（D62）：当前会话内有损压缩",
        "- 长期向量记忆（今天）：跨会话、按需注入",
        "",
        "## 偏好存储与检索",
        "",
        f"- user_id: `{s.user_id}`",
        f"- query: `{s.query}`",
        f"- candidates: {s.candidate_count} / store={s.store_size}",
        f"- returned: {s.returned} (top_k={s.top_k}, min_score={s.min_score})",
        f"- top_score: {s.top_score:.3f}",
        "",
        "## 今日演示统计",
        "",
    ]
    if result.hits:
        lines.append("命中：")
        for h in result.hits:
            lines.append(
                f"- [{h.item.kind}] {h.score:.3f} · {h.item.text}"
            )
    else:
        lines.append("命中：（无）")
    lines.append("")
    lines.append("注入块：")
    lines.append("")
    lines.append(result.context_block or "（无）")
    lines.extend(
        [
            "",
            "## 明日预告",
            "",
            "Day 64 将做记忆写入策略：何时把一句话升级为长期记忆。",
            "",
        ]
    )
    text = "\n".join(lines)
    for section in REQUIRED_REPORT_SECTIONS:
        if f"## {section}" not in text:
            raise RuntimeError(f"missing section: {section}")
    return text
