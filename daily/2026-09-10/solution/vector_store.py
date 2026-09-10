"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


class VectorStoreError(ValueError):
    """向量库参数或状态不合法。"""


@dataclass(frozen=True)
class StoredItem:
    id: str
    document: str
    embedding: tuple[float, ...]
    metadata: Mapping[str, Any]


@dataclass(frozen=True)
class QueryMatch:
    id: str
    document: str
    metadata: Mapping[str, Any]
    score: float
    rank: int


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) == 0 or len(a) != len(b):
        raise VectorStoreError("vector length mismatch")
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


def _as_float_tuple(values: Sequence[float], *, label: str) -> tuple[float, ...]:
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
    def __init__(self, name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise VectorStoreError("collection name must be non-empty str")
        self.name = name.strip()
        self._items: dict[str, StoredItem] = {}
        self._dims: int | None = None

    @property
    def dims(self) -> int | None:
        return self._dims

    def count(self) -> int:
        return len(self._items)

    def add(
        self,
        *,
        ids: Sequence[str],
        documents: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        metadatas: Sequence[Mapping[str, Any]] | None = None,
    ) -> None:
        n = len(ids)
        if n == 0:
            raise VectorStoreError("empty add batch")
        if len(documents) != n or len(embeddings) != n:
            raise VectorStoreError("ids/documents/embeddings length mismatch")
        if metadatas is None:
            meta_list: list[Mapping[str, Any]] = [{} for _ in range(n)]
        else:
            if len(metadatas) != n:
                raise VectorStoreError("metadata length mismatch")
            meta_list = list(metadatas)

        parsed: list[StoredItem] = []
        seen_in_batch: set[str] = set()
        batch_dims: int | None = None

        for i in range(n):
            raw_id = ids[i]
            if not isinstance(raw_id, str) or not raw_id.strip():
                raise VectorStoreError("invalid id")
            item_id = raw_id.strip()
            if item_id in seen_in_batch or item_id in self._items:
                raise VectorStoreError(f"duplicate id: {item_id}")
            seen_in_batch.add(item_id)

            doc = documents[i]
            if not isinstance(doc, str) or not doc.strip():
                raise VectorStoreError("invalid document")

            emb = _as_float_tuple(embeddings[i], label="item")
            if batch_dims is None:
                batch_dims = len(emb)
            elif len(emb) != batch_dims:
                raise VectorStoreError("embedding dims mismatch")

            meta = meta_list[i]
            if not isinstance(meta, Mapping):
                raise VectorStoreError("metadata must be mapping")
            parsed.append(
                StoredItem(
                    id=item_id,
                    document=doc,
                    embedding=emb,
                    metadata=dict(meta),
                )
            )

        assert batch_dims is not None
        if self._dims is not None and batch_dims != self._dims:
            raise VectorStoreError("embedding dims mismatch")

        for item in parsed:
            self._items[item.id] = item
        self._dims = batch_dims

    def query(
        self,
        *,
        query_embeddings: Sequence[Sequence[float]],
        n_results: int = 3,
    ) -> list[list[QueryMatch]]:
        if len(query_embeddings) == 0:
            raise VectorStoreError("query_embeddings must not be empty")
        if isinstance(n_results, bool) or not isinstance(n_results, int) or n_results < 1:
            raise VectorStoreError("n_results must be >= 1")

        results: list[list[QueryMatch]] = []
        for raw_q in query_embeddings:
            if self._dims is None or not self._items:
                results.append([])
                continue

            q = _as_float_tuple(raw_q, label="query")
            if len(q) != self._dims:
                raise VectorStoreError("query embedding dims mismatch")

            scored: list[tuple[float, str, StoredItem]] = []
            for item in self._items.values():
                score = cosine_similarity(q, item.embedding)
                scored.append((score, item.id, item))
            scored.sort(key=lambda t: (-t[0], t[1]))
            top = scored[:n_results]
            matches = [
                QueryMatch(
                    id=item.id,
                    document=item.document,
                    metadata=item.metadata,
                    score=score,
                    rank=rank,
                )
                for rank, (score, _, item) in enumerate(top, start=1)
            ]
            results.append(matches)
        return results


class MiniChromaClient:
    def __init__(self) -> None:
        self._collections: dict[str, MiniCollection] = {}

    def create_collection(self, name: str) -> MiniCollection:
        col = MiniCollection(name)
        if col.name in self._collections:
            raise VectorStoreError(f"collection exists: {col.name}")
        self._collections[col.name] = col
        return col

    def get_or_create_collection(self, name: str) -> MiniCollection:
        col = MiniCollection(name)
        existing = self._collections.get(col.name)
        if existing is not None:
            return existing
        self._collections[col.name] = col
        return col

    def list_collections(self) -> list[str]:
        return sorted(self._collections)
