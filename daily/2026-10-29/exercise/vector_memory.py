"""Day 63 练习：长期向量记忆（跨会话用户偏好）。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——不调用真实 Embedding API，不用 Chroma/FAISS。
"""

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
    """与 PYTHONHASHSEED 无关的稳定分桶（已给齐，勿改）。"""
    h = 2166136261
    for b in token.encode("utf-8"):
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return h % dim


def _l2_normalize(vec: list[float]) -> list[float]:
    """L2 归一化；零向量原样返回。"""
    # TODO
    raise NotImplementedError


def mock_embed(text: str) -> list[float]:
    """确定性教学用 embedding。

    规则：
    1. 非 str → TypeError
    2. strip().lower()；空串 → 全 0 向量（长度 EMBED_DIM）
    3. 每个字符 unigram 桶 +1.0；每个 bigram 桶 +1.5（用 _stable_bucket）
    4. 最后 L2 归一化
    """
    # TODO
    raise NotImplementedError


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """余弦相似度。

    - 非 list/tuple → TypeError
    - 长度 0 或不相等 → ValueError
    - 任一方为零向量 → 0.0
    """
    # TODO
    raise NotImplementedError


def format_memory_block(hits: Sequence[ScoredMemory]) -> str | None:
    """格式化为可注入 prompt 的文本块。

    - 空 hits → None
    - 否则首行 MEMORY_MARKER，随后每条：
      `- ({kind}, score={score:.3f}) {text}`
    """
    # TODO
    raise NotImplementedError


class VectorMemoryStore:
    """进程内长期向量记忆：按 user_id 隔离。"""

    def __init__(self, *, embed_fn: EmbedFn | None = None) -> None:
        # TODO: 保存 embed_fn（默认 mock_embed）与内部 dict
        raise NotImplementedError

    def size(self, user_id: str | None = None) -> int:
        """总条数，或某用户条数。"""
        # TODO
        raise NotImplementedError

    def get(self, memory_id: str) -> MemoryItem | None:
        # TODO
        raise NotImplementedError

    def list_user(self, user_id: str) -> list[MemoryItem]:
        """列出某用户全部记忆；空 user_id → ValueError。"""
        # TODO
        raise NotImplementedError

    def upsert(
        self,
        *,
        user_id: str,
        text: str,
        kind: str = KIND_PREFERENCE,
        memory_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> MemoryItem:
        """写入或覆盖一条记忆。

        - user_id / text strip 后为空 → ValueError
        - kind 非法 → ValueError
        - memory_id 空则自动生成 mem- + 12 位 hex
        - embedding = embed_fn(text)；维度必须为 EMBED_DIM
        """
        # TODO
        raise NotImplementedError

    def remember_preference(
        self,
        user_id: str,
        preference: str,
        *,
        memory_id: str | None = None,
    ) -> MemoryItem:
        """语义糖：kind=preference。"""
        # TODO
        raise NotImplementedError

    def delete(self, memory_id: str) -> bool:
        """删除成功 True，不存在 False。"""
        # TODO
        raise NotImplementedError

    def clear(self, user_id: str | None = None) -> int:
        """清空全部或某用户；返回删除条数。user_id 空串 → ValueError。"""
        # TODO
        raise NotImplementedError

    def search(
        self,
        query: str,
        *,
        user_id: str,
        top_k: int = 3,
        min_score: float = 0.15,
    ) -> RecallResult:
        """在指定用户记忆中语义检索。

        规则：
        1. query / user_id 空 → ValueError；top_k < 1 → ValueError
        2. 只在该 user_id 的条目中算 cosine
        3. score >= min_score 才入候选
        4. 按 score 降序，同分按 id 升序；取前 top_k
        5. context_block = format_memory_block(hits)
        """
        # TODO
        raise NotImplementedError


def build_demo_preferences() -> list[tuple[str, str]]:
    """演示用 (user_id, preference) 列表（已给齐）。"""
    return [
        ("u-front", "我喜欢深色主题，界面尽量少动画"),
        ("u-front", "回答请用中文，代码示例优先 TypeScript"),
        ("u-front", "我在学 Agent，偏好小步可运行练习"),
        ("u-back", "我偏好 Go 语言，不写 Python"),
        ("u-back", "日志用 JSON，不要彩色终端输出"),
    ]


def seed_demo_store(store: VectorMemoryStore | None = None) -> VectorMemoryStore:
    """向 store 写入演示偏好。"""
    # TODO: 若 store 为 None 则新建；按 build_demo_preferences 写入 demo-1..N
    raise NotImplementedError


def render_vector_memory_report(result: RecallResult) -> str:
    """生成 Markdown 报告，必须包含 REQUIRED_REPORT_SECTIONS 里的二级标题。"""
    # TODO
    raise NotImplementedError
