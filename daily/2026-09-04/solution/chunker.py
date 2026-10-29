"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


class ChunkError(ValueError):
    """切分参数或输入非法。"""


@dataclass(frozen=True)
class Document:
    source: str
    text: str


@dataclass(frozen=True)
class Chunk:
    source: str
    index: int
    start: int
    end: int
    text: str
    char_count: int


def validate_chunk_params(chunk_size: int, overlap: int) -> None:
    if chunk_size < 1:
        raise ChunkError("chunk_size must be >= 1")
    if overlap < 0:
        raise ChunkError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise ChunkError("overlap must be < chunk_size")


def chunk_text(
    text: str,
    *,
    chunk_size: int = 200,
    overlap: int = 40,
    source: str = "",
) -> list[Chunk]:
    validate_chunk_params(chunk_size, overlap)
    if text == "":
        return []

    step = chunk_size - overlap
    n = len(text)
    chunks: list[Chunk] = []
    start = 0
    index = 0
    while True:
        end = min(start + chunk_size, n)
        piece = text[start:end]
        chunks.append(
            Chunk(
                source=source,
                index=index,
                start=start,
                end=end,
                text=piece,
                char_count=end - start,
            )
        )
        if end == n:
            break
        start += step
        index += 1
    return chunks


def chunk_document(
    doc: Document,
    *,
    chunk_size: int = 200,
    overlap: int = 40,
) -> list[Chunk]:
    return chunk_text(
        doc.text,
        chunk_size=chunk_size,
        overlap=overlap,
        source=doc.source,
    )


def chunk_corpus(
    docs: Sequence[Document],
    *,
    chunk_size: int = 200,
    overlap: int = 40,
) -> list[Chunk]:
    out: list[Chunk] = []
    for doc in docs:
        out.extend(
            chunk_document(doc, chunk_size=chunk_size, overlap=overlap)
        )
    return out


def chunk_stats(chunks: Sequence[Chunk]) -> dict[str, object]:
    total_chars = sum(c.char_count for c in chunks)
    total = len(chunks)
    by_source: dict[str, int] = {}
    sources: list[str] = []
    seen: set[str] = set()
    for c in chunks:
        by_source[c.source] = by_source.get(c.source, 0) + 1
        if c.source not in seen:
            seen.add(c.source)
            sources.append(c.source)
    ordered = {k: by_source[k] for k in sorted(by_source)}
    avg = (total_chars / total) if total else 0.0
    return {
        "total_chunks": total,
        "total_chars": total_chars,
        "avg_chunk_size": avg,
        "by_source": ordered,
        "sources": sources,
    }
