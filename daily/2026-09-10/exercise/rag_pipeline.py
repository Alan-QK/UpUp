"""Day 36 练习：最小 RAG 生成链路（Retrieve → Augment → Generate）。

复用 Day 34 的 MiniCollection（`vector_store.py` 已给出，勿改）。
请完成 TODO，使 tests/ 全部通过。
只用标准库 + pytest；不要引入 openai / langchain / chromadb。
生成侧通过可注入的 `GenerateFn` 完成——测试与 demo 都用假函数，零费用。
"""

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
    """一条检索命中，进入 Prompt 的上下文单元。"""

    rank: int
    score: float
    source: str
    text: str
    chunk_id: str = ""


@dataclass(frozen=True)
class RagMessage:
    """一条 Chat 消息（role / content）。"""

    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class RagAnswer:
    """一次 RAG 问答结果。"""

    question: str
    answer: str
    contexts: tuple[RetrievedChunk, ...]
    messages: tuple[RagMessage, ...]


class GenerateFn(Protocol):
    """生成回调：吃消息列表，返回助手文本。"""

    def __call__(self, messages: Sequence[RagMessage]) -> str: ...


SYSTEM_PROMPT = (
    "你是一个严谨的问答助手。只根据用户消息里的「参考资料」回答问题。"
    "若资料不足，请明确说不知道。不要编造资料中没有的事实。"
)

# ---------------------------------------------------------------------------
# 已给出：伪 embedding（确定性）—— 勿改
# ---------------------------------------------------------------------------

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


def normalize_question(question: str) -> str:
    """规范化问题：strip；空 → RagError，消息含 \"question\"。"""
    # TODO
    raise NotImplementedError


def match_to_chunk(match: QueryMatch) -> RetrievedChunk:
    """把 VectorStore 的 QueryMatch 转成 RetrievedChunk。

    - source = metadata.get(\"source\", \"?\")
    - text = match.document
    - chunk_id = match.id
    - rank / score 原样保留
    """
    # TODO
    raise NotImplementedError


def format_context_block(chunks: Sequence[RetrievedChunk]) -> str:
    """把检索命中格式化为 Prompt 里的「参考资料」正文。

    规则：
    - chunks 为空 → 返回精确字符串：`(无相关资料)`
    - 否则每条三行（条目之间用一个空行分隔）：
        `[<rank>] source=<source> score=<score四位小数> id=<chunk_id>`
        `<text>`   （原文，不额外 indent）
        （空行，最后一条后面不要多余空行）
    - 末尾无尾随空行；多条之间恰好一个空行
    """
    # TODO
    raise NotImplementedError


def build_rag_messages(
    question: str,
    chunks: Sequence[RetrievedChunk],
) -> list[RagMessage]:
    """拼装 system + user 两条消息（Augment）。

    规则：
    - 先 normalize_question(question)
    - messages[0]：role=system，content=SYSTEM_PROMPT（常量，勿改字）
    - messages[1]：role=user，content 精确为下列模板（注意换行）：

        参考资料：
        <format_context_block 的结果>

        问题：<规范化后的 question>

        请基于参考资料回答。
    """
    # TODO
    raise NotImplementedError


def retrieve(
    collection: MiniCollection,
    query: str,
    *,
    k: int = 3,
    embed_fn: EmbedFn = fake_embed,
) -> list[RetrievedChunk]:
    """Retrieve：对查询做 top-k 语义检索并转为 RetrievedChunk 列表。

    规则：
    - query 先 normalize_question（复用同一校验）
    - k 为 bool 或 <1 → RagError，消息含 \"k\"
    - embed_fn(query) → collection.query(..., n_results=k)
    - 逐条 match_to_chunk；保持 query 返回顺序
    """
    # TODO
    raise NotImplementedError


def run_rag(
    collection: MiniCollection,
    question: str,
    *,
    generate_fn: GenerateFn,
    k: int = 3,
    embed_fn: EmbedFn = fake_embed,
) -> RagAnswer:
    """完整链路：Retrieve → Augment → Generate。

    流程：
    1. contexts = retrieve(...)
    2. messages = build_rag_messages(question, contexts)
    3. answer = generate_fn(messages)；须为 str
       - 若返回值不是 str → RagError，消息含 \"generate\"
       - 若 strip 后为空 → RagError，消息含 \"empty\"
    4. 返回 RagAnswer(
         question=规范化后的问题,
         answer=answer.strip(),
         contexts=tuple(contexts),
         messages=tuple(messages),
       )
    """
    # TODO
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 已给出：知识库装载（练习脚手架）—— 勿改
# ---------------------------------------------------------------------------


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
    """把 fixtures 知识库整篇写入 collection（一篇文档 = 一个 chunk，简化）。

    返回写入条数。空目录 → RagError，消息含 \"no documents\"。
    """
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
    """演示用假生成器：从 user 消息里抠第一段参考资料摘要作答。"""
    if len(messages) < 2:
        return "不知道"
    user = messages[1].content
    if "(无相关资料)" in user:
        return "不知道：参考资料不足。"
    # 取第一条资料的正文第一行非空内容
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
