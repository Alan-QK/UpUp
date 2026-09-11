"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import hashlib
import math
import struct
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from vector_store import MiniCollection, QueryMatch

SUPPORTED_SUFFIXES: tuple[str, ...] = (".txt", ".md", ".markdown")

EmbedFn = Callable[[str], list[float]]


class RagError(ValueError):
    """RAG 参数或状态不合法。"""


@dataclass(frozen=True)
class RetrievedChunk:
    rank: int
    score: float
    source: str
    text: str
    chunk_id: str = ""


@dataclass(frozen=True)
class RagMessage:
    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class RagAnswer:
    question: str
    answer: str
    contexts: tuple[RetrievedChunk, ...]
    messages: tuple[RagMessage, ...]


class GenerateFn(Protocol):
    def __call__(self, messages: Sequence[RagMessage]) -> str: ...


SYSTEM_PROMPT = (
    "你是一个严谨的问答助手。只根据用户消息里的「参考资料」回答问题。"
    "若资料不足，请明确说不知道。不要编造资料中没有的事实。"
)

_TOPIC_ANCHORS: list[tuple[str, int]] = [
    ("向量", 0),
    ("检索", 1),
    ("Retrieve", 1),
    ("retrieve", 1),
    ("top-k", 1),
    ("RAG", 2),
    ("rag", 2),
    ("Augment", 2),
    ("Generate", 2),
    ("Prompt", 3),
    ("prompt", 3),
    ("参考资料", 3),
    ("引用", 3),
    ("前端", 4),
    ("SSE", 4),
    ("Python", 5),
    ("pytest", 5),
    ("dataclass", 5),
    ("幻觉", 6),
    ("溯源", 6),
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


def normalize_question(question: str) -> str:
    q = question.strip()
    if not q:
        raise RagError("question must be non-empty")
    return q


def match_to_chunk(match: QueryMatch) -> RetrievedChunk:
    source = str(match.metadata.get("source", "?"))
    return RetrievedChunk(
        rank=match.rank,
        score=match.score,
        source=source,
        text=match.document,
        chunk_id=match.id,
    )


def format_context_block(chunks: Sequence[RetrievedChunk]) -> str:
    if not chunks:
        return "(无相关资料)"
    parts: list[str] = []
    for c in chunks:
        header = (
            f"[{c.rank}] source={c.source} "
            f"score={c.score:.4f} id={c.chunk_id}"
        )
        parts.append(f"{header}\n{c.text}")
    return "\n\n".join(parts)


def build_rag_messages(
    question: str,
    chunks: Sequence[RetrievedChunk],
) -> list[RagMessage]:
    q = normalize_question(question)
    block = format_context_block(chunks)
    user = (
        f"参考资料：\n{block}\n\n"
        f"问题：{q}\n\n"
        "请基于参考资料回答。"
    )
    return [
        RagMessage(role="system", content=SYSTEM_PROMPT),
        RagMessage(role="user", content=user),
    ]


def retrieve(
    collection: MiniCollection,
    query: str,
    *,
    k: int = 3,
    embed_fn: EmbedFn = fake_embed,
) -> list[RetrievedChunk]:
    q = normalize_question(query)
    if isinstance(k, bool) or k < 1:
        raise RagError("k must be >= 1")
    matches = collection.query(
        query_embeddings=[embed_fn(q)],
        n_results=k,
    )[0]
    return [match_to_chunk(m) for m in matches]


def run_rag(
    collection: MiniCollection,
    question: str,
    *,
    generate_fn: GenerateFn,
    k: int = 3,
    embed_fn: EmbedFn = fake_embed,
) -> RagAnswer:
    contexts = retrieve(collection, question, k=k, embed_fn=embed_fn)
    messages = build_rag_messages(question, contexts)
    raw = generate_fn(messages)
    if not isinstance(raw, str):
        raise RagError("generate must return str")
    answer = raw.strip()
    if not answer:
        raise RagError("empty generation")
    return RagAnswer(
        question=normalize_question(question),
        answer=answer,
        contexts=tuple(contexts),
        messages=tuple(messages),
    )


def _discover_files(root: Path) -> list[Path]:
    root = root.resolve()
    if not root.is_dir():
        raise RagError("not a directory")
    found: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        found.append(path)
    found.sort(key=lambda p: p.relative_to(root).as_posix())
    return found


def index_kb_dir(
    root: Path,
    collection: MiniCollection,
    *,
    embed_fn: EmbedFn = fake_embed,
) -> int:
    paths = _discover_files(root)
    if not paths:
        raise RagError("no documents")
    root = root.resolve()
    ids: list[str] = []
    documents: list[str] = []
    embeddings: list[list[float]] = []
    metadatas: list[dict[str, str]] = []
    for path in paths:
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
        text = text.lstrip("\ufeff").strip()
        if not text:
            continue
        source = path.relative_to(root).as_posix()
        chunk_id = f"{source}#0"
        ids.append(chunk_id)
        documents.append(text)
        embeddings.append(embed_fn(text))
        metadatas.append({"source": source})
    if not ids:
        raise RagError("no documents")
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(ids)


def demo_generate(messages: Sequence[RagMessage]) -> str:
    if len(messages) < 2:
        return "不知道"
    user = messages[1].content
    if "(无相关资料)" in user:
        return "不知道：参考资料不足。"
    lines = user.splitlines()
    body_lines: list[str] = []
    capture = False
    for line in lines:
        if line.startswith("[1] "):
            capture = True
            continue
        if capture:
            if line.startswith("[") and "] source=" in line:
                break
            if line.startswith("问题："):
                break
            if line.strip():
                body_lines.append(line.strip())
            elif body_lines:
                break
    if not body_lines:
        return "不知道：未能解析参考资料。"
    snippet = body_lines[0][:80]
    return f"根据参考资料：{snippet}"
