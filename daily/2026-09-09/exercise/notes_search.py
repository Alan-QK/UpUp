"""Day 35 练习：本地笔记检索 CLI（Week 7 周挑战）。

串起：发现文件 → 加载 → 切分 → 伪向量 → MiniCollection → top-k 检索。
`vector_store.py` 与下方假 embedding / dataclass **已给出，请勿修改**。
请完成 TODO，使 tests/ 全部通过。
只用标准库 + pytest；不要引入 chromadb / numpy / openai / langchain。
"""

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
    """一篇笔记（相对路径 + 正文）。"""

    source: str
    text: str


@dataclass(frozen=True)
class Chunk:
    """一篇笔记切出的片段。"""

    source: str
    index: int
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class IndexReport:
    """一次建索引的统计。"""

    files: int
    chunks: int
    skipped_empty: int


@dataclass(frozen=True)
class SearchHit:
    """一条检索命中（面向 CLI 展示）。"""

    rank: int
    score: float
    id: str
    source: str
    chunk_index: int
    text: str


# ---------------------------------------------------------------------------
# 已给出：伪 embedding（确定性，无网络）—— 勿改
# ---------------------------------------------------------------------------

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
    """确定性伪向量：相同文本 → 相同向量；共享关键词时更靠近（仅练习）。"""
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
    """校验切分参数；非法 → NotesSearchError（消息含关键字）。"""
    if chunk_size < 1:
        raise NotesSearchError("chunk_size must be >= 1")
    if overlap < 0:
        raise NotesSearchError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise NotesSearchError("overlap must be < chunk_size")


def make_chunk_id(source: str, index: int) -> str:
    """稳定 chunk id：`<source>#<index>`。"""
    return f"{source}#{index}"


# ---------------------------------------------------------------------------
# TODO：请实现
# ---------------------------------------------------------------------------


def discover_notes(root: Path) -> list[Path]:
    """递归发现笔记文件，返回绝对 Path 列表（按相对 posix 路径排序）。

    规则：
    - 只收后缀在 SUPPORTED_SUFFIXES 中的文件（小写比较）
    - 任一路径分量以 '.' 开头 → 整条路径跳过（含隐藏文件/目录）
    - root 不是目录 → NotesSearchError，消息含 \"not a directory\"
    - 先 Path(root).resolve()；返回的是绝对路径
    """
    # TODO
    raise NotImplementedError


def load_note(path: Path, *, root: Path) -> NoteDoc:
    """加载单篇笔记。

    规则：
    - 先把 path / root 都 resolve，再算相对路径（避免绝对/相对混用报错）
    - source = path 相对 root 的 posix 字符串（Path.as_posix）
    - 以 UTF-8 读取；失败 → NotesSearchError，消息含 \"utf-8\"
    - 去掉开头 BOM（\\ufeff）；\\r\\n / \\r → \\n
    - 文本 strip 后若为空 → NotesSearchError，消息含 \"empty\"
    - path 不是文件 → NotesSearchError，消息含 \"not a file\"
    """
    # TODO
    raise NotImplementedError


def chunk_text(
    text: str,
    *,
    chunk_size: int = 120,
    overlap: int = 20,
    source: str = "",
) -> list[Chunk]:
    """固定窗口 + overlap 切分（半开区间 [start, end)）。

    规则：
    - 先 validate_chunk_params
    - 空串 → []
    - step = chunk_size - overlap
    - 每块：index 从 0 递增；end == len(text) 后停止
    - Chunk.text 为 text[start:end]；不要再 strip
    """
    # TODO
    raise NotImplementedError


def chunk_note(
    doc: NoteDoc,
    *,
    chunk_size: int = 120,
    overlap: int = 20,
) -> list[Chunk]:
    """对一篇 NoteDoc 切分。"""
    # TODO
    raise NotImplementedError


def index_documents(
    docs: Sequence[NoteDoc],
    collection: MiniCollection,
    *,
    chunk_size: int = 120,
    overlap: int = 20,
    embed_fn: EmbedFn = fake_embed,
) -> IndexReport:
    """把多篇笔记写入 collection。

    流程：
    1. 对每篇 chunk_note；空 chunk 列表计入 skipped_empty（该文件仍算 files）
    2. 为每个 chunk 生成 id=make_chunk_id(source, index)
    3. metadata = {\"source\": source, \"index\": index, \"start\": start, \"end\": end}
    4. 一次性（或分批均可）collection.add；本练习允许一次 add 全部 chunk
    5. 若最终没有任何 chunk → NotesSearchError，消息含 \"no chunks\"
    6. 返回 IndexReport(files=len(docs), chunks=总块数, skipped_empty=空正文篇数)

    注意：docs 为空列表 → NotesSearchError，消息含 \"empty\"
    """
    # TODO
    raise NotImplementedError


def index_notes_dir(
    root: Path,
    collection: MiniCollection,
    *,
    chunk_size: int = 120,
    overlap: int = 20,
    embed_fn: EmbedFn = fake_embed,
) -> IndexReport:
    """发现目录下笔记 → 加载 → 建索引。

    - 先 resolve(root)，再 discover_notes + load_note
    - 若发现 0 个文件 → NotesSearchError，消息含 \"no notes\"
    """
    # TODO
    raise NotImplementedError


def search_notes(
    collection: MiniCollection,
    query: str,
    *,
    k: int = 3,
    embed_fn: EmbedFn = fake_embed,
) -> list[SearchHit]:
    """对查询文本做 top-k 语义检索。

    规则：
    - query strip 后为空 → NotesSearchError，消息含 \"query\"
    - k 非法（bool 或 <1）→ NotesSearchError，消息含 \"k\"
    - 用 embed_fn(query) 得到向量，调用 collection.query
    - 把 QueryMatch 转成 SearchHit：
      source = metadata[\"source\"]（缺省 \"?\"）
      chunk_index = int(metadata[\"index\"])（缺省 -1）
      text = document
    - 保持 rank / score / id
    """
    # TODO
    raise NotImplementedError


def format_hits(hits: Sequence[SearchHit], *, query: str = "") -> str:
    """渲染 CLI 可读结果。

    格式约定（测试会检查关键片段）：
    - 第一行：`query: <query>`（若 query 非空）或 `query: (empty)`
    - 若 hits 为空：下一行 `no hits`
    - 否则每条命中两行：
      `#<rank>  score=<score四位小数>  source=<source>#<chunk_index>  id=<id>`
      `       <text>`（注意 text 前有 7 个空格缩进）
    - 末尾不要多余空行（最后一行可以是最后一条的 text，无尾随 \\n\\n）
    """
    # TODO
    raise NotImplementedError
