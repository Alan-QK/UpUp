"""Day 34 练习：对齐 Chroma 心智的内存向量 Collection。

请完成 TODO，使 tests/ 全部通过。
只用标准库；不要引入 chromadb / numpy / langchain。
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


class VectorStoreError(ValueError):
    """向量库参数或状态不合法。"""


@dataclass(frozen=True)
class StoredItem:
    """Collection 内的一条记录。"""

    id: str
    document: str
    embedding: tuple[float, ...]
    metadata: Mapping[str, Any]


@dataclass(frozen=True)
class QueryMatch:
    """一次 top-k 命中。"""

    id: str
    document: str
    metadata: Mapping[str, Any]
    score: float
    rank: int


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """计算余弦相似度。

    规则：
    - 长度必须相同且 > 0，否则 VectorStoreError，消息含 \"length\"
    - 任一向量 L2 模长为 0 → 返回 0.0（避免除零）
    - 否则返回 dot / (norm_a * norm_b)
    """
    # TODO
    raise NotImplementedError


def _as_float_tuple(values: Sequence[float], *, label: str) -> tuple[float, ...]:
    """把序列转成 float tuple；非法则 VectorStoreError（消息含 label 与 \"embedding\"）。

    已实现，可直接在 add/query 里复用；也可以自己内联，不必改此函数。
    """
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise VectorStoreError(f"invalid {label} embedding")
    if len(values) == 0:
        raise VectorStoreError(f"invalid {label} embedding")
    out: list[float] = []
    for item in values:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise VectorStoreError(f"invalid {label} embedding")
        out.append(float(item))
    return tuple(out)


class MiniCollection:
    """内存版 Collection：语义对齐 Chroma 的 add / query。

    - 首次成功 add 后锁定 embedding 维度（dims）
    - id 全局唯一（本 collection 内）
    - query 按余弦相似度降序；同分比 id 升序；rank 从 1 起
    """

    def __init__(self, name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise VectorStoreError("collection name must be non-empty str")
        self.name = name.strip()
        self._items: dict[str, StoredItem] = {}
        self._dims: int | None = None

    @property
    def dims(self) -> int | None:
        """当前锁定的向量维度；尚未写入时为 None。"""
        return self._dims

    def count(self) -> int:
        """返回已存储条数。"""
        # TODO
        raise NotImplementedError

    def add(
        self,
        *,
        ids: Sequence[str],
        documents: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        metadatas: Sequence[Mapping[str, Any]] | None = None,
    ) -> None:
        """写入一批记录。

        规则（消息需包含对应关键字，便于测试 match）：
        - ids / documents / embeddings 长度必须相同，且 > 0
          · 长度不一致 → VectorStoreError，消息含 \"length\"
          · 空批次 → VectorStoreError，消息含 \"empty\"
        - metadatas 为 None 时，视为每条 `{}`
          · 若提供，则长度必须与 ids 相同，否则消息含 \"metadata\"
        - 每个 id 必须是非空 str（strip 后非空）；否则消息含 \"id\"
        - 同一批次或与已有数据 id 重复 → VectorStoreError，消息含 \"duplicate\"
        - 每个 document 必须是 str（允许空串？→ 不允许 strip 后为空）
          · 非 str 或 blank → 消息含 \"document\"
        - 每个 embedding：非空、元素为 int/float（非 bool）、维度一致
          · 坏向量 → 消息含 \"embedding\"
          · 与已锁定 dims 或批次内 dims 不一致 → 消息含 \"dims\"
        - 成功写入后更新 self._dims
        - metadata 存入时用 dict(...) 浅拷贝，避免外部可变 dict 被后续修改污染
        """
        # TODO
        raise NotImplementedError

    def query(
        self,
        *,
        query_embeddings: Sequence[Sequence[float]],
        n_results: int = 3,
    ) -> list[list[QueryMatch]]:
        """对每个查询向量做 top-k。

        规则：
        - query_embeddings 不能为空 → VectorStoreError，消息含 \"empty\"
        - n_results 必须是 int 且 >= 1（bool 不算合法 int）→ 消息含 \"n_results\"
        - 若库为空：对每个 query 返回 []（不报错）
        - 每个 query embedding：
          · 校验为合法 float 序列；维度必须等于 self._dims → 否则消息含 \"dims\" 或 \"embedding\"
        - 评分：cosine_similarity；降序；同分按 id 升序
        - 每条 QueryMatch.rank 从 1 开始（对该 query 的结果列表而言）
        - 返回外层 list 长度 = len(query_embeddings)；内层长度 = min(n_results, count)
        """
        # TODO
        raise NotImplementedError


class MiniChromaClient:
    """极简 Client：按名称管理多个 MiniCollection。"""

    def __init__(self) -> None:
        self._collections: dict[str, MiniCollection] = {}

    def create_collection(self, name: str) -> MiniCollection:
        """创建集合；同名已存在 → VectorStoreError，消息含 \"exists\"。"""
        # TODO
        raise NotImplementedError

    def get_or_create_collection(self, name: str) -> MiniCollection:
        """获取或创建集合。"""
        # TODO
        raise NotImplementedError

    def list_collections(self) -> list[str]:
        """返回集合名，按字母序。"""
        # TODO
        raise NotImplementedError
