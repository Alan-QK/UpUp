"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import hashlib
import math
import struct
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vector_store import MiniCollection, QueryMatch, VectorStoreError

SUPPORTED_SUFFIXES: tuple[str, ...] = (".txt", ".md", ".markdown")

EmbedFn = Callable[[str], list[float]]


class NotesSearchError(ValueError):
    """笔记索引 / 检索参数不合法。"""


@dataclass(frozen=True)
class NoteDoc:
    source: str
    text: str


@dataclass(frozen=True)
class Chunk:
    source: str
    index: int
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class IndexReport:
    files: int
    chunks: int
    skipped_empty: int


@dataclass(frozen=True)
class SearchHit:
    rank: int
    score: float
    id: str
    source: str
    chunk_index: int
    text: str


_TOPIC_ANCHORS: list[tuple[str, int]] = [
    ("向量", 0),
    ("检索", 1),
    ("top-k", 1),
    ("topk", 1),
    ("RAG", 2),
    ("rag", 2),
    ("Chroma", 3),
    ("chroma", 3),
    ("Collection", 3),
    ("embedding", 4),
    ("前端", 5),
    ("SSE", 5),
    ("Python", 6),
    ("pytest", 6),
    ("dataclass", 6),
    ("pathlib", 6),
    ("Agent", 7),
    ("工具", 7),
]


def fake_embed(text: str, dims: int = 16) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    vals: list[float] = []
    seed = digest
    while len(vals) < dims:
        for i in range(0, len(seed) - (len(seed) % 4), 4):
            raw = struct.unpack_from("!I", seed, i)[0]
            vals.append((raw / 0xFFFFFFFF) * 2.0 - 1.0)
            if len(vals) >= dims:
                break
        seed = hashlib.sha256(seed).digest()
    boost = [0.0] * dims
    for i in range(len(text) - 1):
        h = hash(text[i : i + 2]) % dims
        boost[h] += 0.08
    lower = text.lower()
    for token, axis in _TOPIC_ANCHORS:
        if token.lower() in lower:
            boost[axis % dims] += 1.6
    vec = [vals[i] * 0.15 + boost[i] for i in range(dims)]
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def validate_chunk_params(chunk_size: int, overlap: int) -> None:
    if chunk_size < 1:
        raise NotesSearchError("chunk_size must be >= 1")
    if overlap < 0:
        raise NotesSearchError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise NotesSearchError("overlap must be < chunk_size")


def make_chunk_id(source: str, index: int) -> str:
    return f"{source}#{index}"


def discover_notes(root: Path) -> list[Path]:
    root = Path(root).resolve()
    if not root.is_dir():
        raise NotesSearchError("not a directory")

    found: list[tuple[str, Path]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        found.append((rel.as_posix(), path.resolve()))

    found.sort(key=lambda t: t[0])
    return [p for _, p in found]


def load_note(path: Path, *, root: Path) -> NoteDoc:
    path = Path(path).resolve()
    root = Path(root).resolve()
    if not path.is_file():
        raise NotesSearchError("not a file")
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise NotesSearchError("utf-8") from exc

    if raw.startswith("\ufeff"):
        raw = raw[1:]
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    if text.strip() == "":
        raise NotesSearchError("empty")

    source = path.relative_to(root).as_posix()
    return NoteDoc(source=source, text=text)


def chunk_text(
    text: str,
    *,
    chunk_size: int = 120,
    overlap: int = 20,
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
        chunks.append(
            Chunk(
                source=source,
                index=index,
                start=start,
                end=end,
                text=text[start:end],
            )
        )
        if end == n:
            break
        start += step
        index += 1
    return chunks


def chunk_note(
    doc: NoteDoc,
    *,
    chunk_size: int = 120,
    overlap: int = 20,
) -> list[Chunk]:
    return chunk_text(
        doc.text,
        chunk_size=chunk_size,
        overlap=overlap,
        source=doc.source,
    )


def index_documents(
    docs: Sequence[NoteDoc],
    collection: MiniCollection,
    *,
    chunk_size: int = 120,
    overlap: int = 20,
    embed_fn: EmbedFn = fake_embed,
) -> IndexReport:
    if len(docs) == 0:
        raise NotesSearchError("empty docs")

    all_chunks: list[Chunk] = []
    skipped_empty = 0
    for doc in docs:
        pieces = chunk_note(doc, chunk_size=chunk_size, overlap=overlap)
        if not pieces:
            skipped_empty += 1
            continue
        all_chunks.extend(pieces)

    if not all_chunks:
        raise NotesSearchError("no chunks")

    ids = [make_chunk_id(c.source, c.index) for c in all_chunks]
    documents = [c.text for c in all_chunks]
    embeddings = [embed_fn(c.text) for c in all_chunks]
    metadatas: list[dict[str, Any]] = [
        {
            "source": c.source,
            "index": c.index,
            "start": c.start,
            "end": c.end,
        }
        for c in all_chunks
    ]
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return IndexReport(
        files=len(docs),
        chunks=len(all_chunks),
        skipped_empty=skipped_empty,
    )


def index_notes_dir(
    root: Path,
    collection: MiniCollection,
    *,
    chunk_size: int = 120,
    overlap: int = 20,
    embed_fn: EmbedFn = fake_embed,
) -> IndexReport:
    root = Path(root).resolve()
    paths = discover_notes(root)
    if not paths:
        raise NotesSearchError("no notes")
    docs = [load_note(p, root=root) for p in paths]
    return index_documents(
        docs,
        collection,
        chunk_size=chunk_size,
        overlap=overlap,
        embed_fn=embed_fn,
    )


def search_notes(
    collection: MiniCollection,
    query: str,
    *,
    k: int = 3,
    embed_fn: EmbedFn = fake_embed,
) -> list[SearchHit]:
    if not isinstance(query, str) or query.strip() == "":
        raise NotesSearchError("query must be non-empty")
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise NotesSearchError("k must be >= 1")

    q_vec = embed_fn(query.strip())
    try:
        matches: list[QueryMatch] = collection.query(
            query_embeddings=[q_vec],
            n_results=k,
        )[0]
    except VectorStoreError as exc:
        raise NotesSearchError(str(exc)) from exc

    hits: list[SearchHit] = []
    for m in matches:
        source = str(m.metadata.get("source", "?"))
        raw_index = m.metadata.get("index", -1)
        try:
            chunk_index = int(raw_index)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            chunk_index = -1
        hits.append(
            SearchHit(
                rank=m.rank,
                score=m.score,
                id=m.id,
                source=source,
                chunk_index=chunk_index,
                text=m.document,
            )
        )
    return hits


def format_hits(hits: Sequence[SearchHit], *, query: str = "") -> str:
    q_line = f"query: {query}" if query else "query: (empty)"
    if not hits:
        return f"{q_line}\nno hits"

    lines = [q_line]
    for h in hits:
        lines.append(
            f"#{h.rank}  score={h.score:.4f}  "
            f"source={h.source}#{h.chunk_index}  id={h.id}"
        )
        lines.append(f"       {h.text}")
    return "\n".join(lines)
