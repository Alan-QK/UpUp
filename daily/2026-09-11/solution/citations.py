"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from rag_pipeline import RetrievedChunk

_CITATION_RE = re.compile(r"\[(\d+)\]")


class CitationError(ValueError):
    """引用参数或状态不合法。"""


@dataclass(frozen=True)
class Citation:
    rank: int
    source: str
    chunk_id: str
    score: float
    snippet: str


@dataclass(frozen=True)
class CitedAnswer:
    question: str
    answer: str
    citations: tuple[Citation, ...]
    cited_ranks: tuple[int, ...]
    display: str


def make_snippet(text: str, *, max_chars: int = 72) -> str:
    if isinstance(max_chars, bool) or max_chars < 1:
        raise CitationError("max_chars must be >= 1")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    collapsed = " ".join(normalized.split())
    if len(collapsed) <= max_chars:
        return collapsed
    return collapsed[:max_chars] + "…"


def citations_from_chunks(
    chunks: Sequence[RetrievedChunk],
    *,
    max_chars: int = 72,
) -> list[Citation]:
    return [
        Citation(
            rank=c.rank,
            source=c.source,
            chunk_id=c.chunk_id,
            score=c.score,
            snippet=make_snippet(c.text, max_chars=max_chars),
        )
        for c in chunks
    ]


def parse_cited_ranks(answer: str) -> list[int]:
    seen: set[int] = set()
    ranks: list[int] = []
    for match in _CITATION_RE.finditer(answer):
        n = int(match.group(1))
        if n < 1 or n in seen:
            continue
        seen.add(n)
        ranks.append(n)
    return ranks


def select_citations(
    citations: Sequence[Citation],
    ranks: Sequence[int],
    *,
    mode: str = "mentioned",
) -> list[Citation]:
    if mode == "all":
        return list(citations)
    if mode != "mentioned":
        raise CitationError("mode must be 'mentioned' or 'all'")
    by_rank = {c.rank: c for c in citations}
    selected: list[Citation] = []
    seen: set[int] = set()
    for rank in ranks:
        if rank in seen:
            continue
        if rank not in by_rank:
            raise CitationError(f"unknown citation rank: {rank}")
        seen.add(rank)
        selected.append(by_rank[rank])
    return selected


def format_sources_block(citations: Sequence[Citation]) -> str:
    if not citations:
        return "(无引用)"
    parts: list[str] = ["来源："]
    for c in citations:
        header = (
            f"[{c.rank}] source={c.source} "
            f"id={c.chunk_id} score={c.score:.4f}"
        )
        parts.append(f"{header}\n    {c.snippet}")
    # first line is 来源： then entries joined by blank line
    body = "\n\n".join(parts[1:])
    return f"{parts[0]}\n{body}"


def build_cited_answer(
    question: str,
    answer: str,
    chunks: Sequence[RetrievedChunk],
    *,
    mode: str = "mentioned",
    max_chars: int = 72,
) -> CitedAnswer:
    q = question.strip()
    if not q:
        raise CitationError("question must be non-empty")
    a = answer.strip()
    if not a:
        raise CitationError("empty answer")
    all_citations = citations_from_chunks(chunks, max_chars=max_chars)
    cited_ranks = parse_cited_ranks(a)
    selected = select_citations(all_citations, cited_ranks, mode=mode)
    display = f"{a}\n\n{format_sources_block(selected)}"
    return CitedAnswer(
        question=q,
        answer=a,
        citations=tuple(selected),
        cited_ranks=tuple(cited_ranks),
        display=display,
    )
