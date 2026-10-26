"""Day 37 tests：引用溯源（纯本地）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from citations import (
    Citation,
    CitationError,
    CitedAnswer,
    build_cited_answer,
    citations_from_chunks,
    format_sources_block,
    make_snippet,
    parse_cited_ranks,
    select_citations,
)
from rag_pipeline import RetrievedChunk, demo_generate, index_kb_dir, run_rag
from vector_store import MiniChromaClient

FIX_KB = Path(__file__).resolve().parent.parent / "fixtures" / "kb"


def test_make_snippet_collapse_and_truncate() -> None:
    assert make_snippet("  hello\n\nworld  ") == "hello world"
    long = "a" * 80
    out = make_snippet(long, max_chars=10)
    assert out == "aaaaaaaaaa…"
    assert len(out) == 11


def test_make_snippet_bad_max_chars() -> None:
    with pytest.raises(CitationError, match="max_chars"):
        make_snippet("x", max_chars=0)
    with pytest.raises(CitationError, match="max_chars"):
        make_snippet("x", max_chars=True)  # type: ignore[arg-type]


def test_citations_from_chunks() -> None:
    chunks = [
        RetrievedChunk(1, 0.91234, "a.md", "第一段\n第二行", "a.md#0"),
        RetrievedChunk(2, 0.5, "b.md", "短", "b.md#0"),
    ]
    cites = citations_from_chunks(chunks, max_chars=6)
    # "第一段\n第二行" → "第一段 第二行" → 截断 6 字 + …
    assert cites == [
        Citation(1, "a.md", "a.md#0", 0.91234, "第一段 第二…"),
        Citation(2, "b.md", "b.md#0", 0.5, "短"),
    ]


def test_parse_cited_ranks_order_and_dedupe() -> None:
    assert parse_cited_ranks("参见[2]与[1]，还有[2]和[0]以及[1]。") == [2, 1]
    assert parse_cited_ranks("没有任何括号数字") == []
    assert parse_cited_ranks("边界[12][3]") == [12, 3]


def test_select_citations_mentioned_and_all() -> None:
    cites = [
        Citation(1, "a.md", "a.md#0", 0.9, "A"),
        Citation(2, "b.md", "b.md#0", 0.8, "B"),
        Citation(3, "c.md", "c.md#0", 0.7, "C"),
    ]
    assert select_citations(cites, [2, 1, 2], mode="mentioned") == [
        cites[1],
        cites[0],
    ]
    assert select_citations(cites, [], mode="mentioned") == []
    assert select_citations(cites, [9], mode="all") == cites
    with pytest.raises(CitationError, match="unknown"):
        select_citations(cites, [9], mode="mentioned")
    with pytest.raises(CitationError, match="mode"):
        select_citations(cites, [1], mode="maybe")


def test_format_sources_block() -> None:
    assert format_sources_block([]) == "(无引用)"
    cites = [
        Citation(1, "a.md", "a.md#0", 0.91234, "第一段"),
        Citation(2, "b.md", "b.md#0", 0.8, "第二段"),
    ]
    text = format_sources_block(cites)
    assert text == (
        "来源：\n"
        "[1] source=a.md id=a.md#0 score=0.9123\n"
        "    第一段\n"
        "\n"
        "[2] source=b.md id=b.md#0 score=0.8000\n"
        "    第二段"
    )


def test_build_cited_answer_mentioned() -> None:
    chunks = [
        RetrievedChunk(1, 0.9, "rag_basics.md", "RAG 三步说明", "rag_basics.md#0"),
        RetrievedChunk(2, 0.8, "frontend.md", "SSE 引用面板", "frontend.md#0"),
    ]
    result = build_cited_answer(
        "  什么是 RAG？ ",
        "  RAG 先检索再生成[1]，前端可展示引用[2]。  ",
        chunks,
        mode="mentioned",
        max_chars=20,
    )
    assert isinstance(result, CitedAnswer)
    assert result.question == "什么是 RAG？"
    assert result.answer == "RAG 先检索再生成[1]，前端可展示引用[2]。"
    assert result.cited_ranks == (1, 2)
    assert len(result.citations) == 2
    assert result.citations[0].source == "rag_basics.md"
    assert result.citations[1].source == "frontend.md"
    assert result.display.startswith(result.answer)
    assert "来源：" in result.display
    assert "rag_basics.md" in result.display
    assert "frontend.md" in result.display


def test_build_cited_answer_no_markers_mentioned() -> None:
    chunks = [RetrievedChunk(1, 1.0, "a.md", "正文", "a.md#0")]
    result = build_cited_answer("q", "没有引用标记的答案", chunks, mode="mentioned")
    assert result.cited_ranks == ()
    assert result.citations == ()
    assert result.display.endswith("(无引用)")


def test_build_cited_answer_mode_all() -> None:
    chunks = [
        RetrievedChunk(1, 0.9, "a.md", "A", "a.md#0"),
        RetrievedChunk(2, 0.8, "b.md", "B", "b.md#0"),
    ]
    result = build_cited_answer("q", "答案正文无标记", chunks, mode="all")
    assert result.cited_ranks == ()
    assert len(result.citations) == 2
    assert "来源：" in result.display
    assert "[1]" in result.display and "[2]" in result.display


def test_build_cited_answer_errors() -> None:
    chunks = [RetrievedChunk(1, 1.0, "a.md", "t", "a.md#0")]
    with pytest.raises(CitationError, match="question"):
        build_cited_answer("  ", "有答案[1]", chunks)
    with pytest.raises(CitationError, match="empty"):
        build_cited_answer("q", "   ", chunks)
    with pytest.raises(CitationError, match="unknown"):
        build_cited_answer("q", "引用了不存在的[9]", chunks, mode="mentioned")


def test_integration_with_run_rag() -> None:
    """端到端：假生成带 [1]，再挂上来源。"""
    client = MiniChromaClient()
    col = client.get_or_create_collection("day37")
    index_kb_dir(FIX_KB, col)

    def citing_generate(messages):  # noqa: ANN001
        base = demo_generate(messages)
        return f"{base}[1]"

    rag = run_rag(col, "RAG 为什么能降低幻觉", generate_fn=citing_generate, k=2)
    cited = build_cited_answer(rag.question, rag.answer, rag.contexts, mode="mentioned")
    assert cited.cited_ranks == (1,)
    assert len(cited.citations) == 1
    assert cited.citations[0].rank == 1
    assert cited.citations[0].source
    assert "来源：" in cited.display
