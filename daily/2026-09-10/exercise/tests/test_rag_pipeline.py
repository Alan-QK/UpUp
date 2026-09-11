"""Day 36 tests：最小 RAG 链路（纯本地，假 generate_fn）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from rag_pipeline import (
    SYSTEM_PROMPT,
    RagAnswer,
    RagError,
    RagMessage,
    RetrievedChunk,
    build_rag_messages,
    demo_generate,
    format_context_block,
    index_kb_dir,
    match_to_chunk,
    normalize_question,
    retrieve,
    run_rag,
)
from vector_store import MiniChromaClient, QueryMatch

FIX_KB = Path(__file__).resolve().parent.parent / "fixtures" / "kb"


def test_normalize_question_ok_and_empty() -> None:
    assert normalize_question("  hello  ") == "hello"
    with pytest.raises(RagError, match="question"):
        normalize_question("   ")


def test_match_to_chunk() -> None:
    m = QueryMatch(
        id="a.md#0",
        document="hello",
        metadata={"source": "a.md"},
        score=0.9,
        rank=1,
    )
    c = match_to_chunk(m)
    assert c == RetrievedChunk(
        rank=1,
        score=0.9,
        source="a.md",
        text="hello",
        chunk_id="a.md#0",
    )


def test_match_to_chunk_missing_source() -> None:
    m = QueryMatch(
        id="x",
        document="t",
        metadata={},
        score=0.1,
        rank=2,
    )
    assert match_to_chunk(m).source == "?"


def test_format_context_block_empty() -> None:
    assert format_context_block([]) == "(无相关资料)"


def test_format_context_block_two_chunks() -> None:
    chunks = [
        RetrievedChunk(1, 0.91234, "a.md", "第一段", "a.md#0"),
        RetrievedChunk(2, 0.8, "b.md", "第二段", "b.md#0"),
    ]
    text = format_context_block(chunks)
    assert text == (
        "[1] source=a.md score=0.9123 id=a.md#0\n"
        "第一段\n"
        "\n"
        "[2] source=b.md score=0.8000 id=b.md#0\n"
        "第二段"
    )


def test_build_rag_messages_shape() -> None:
    chunks = [RetrievedChunk(1, 1.0, "rag_basics.md", "RAG 三步", "rag_basics.md#0")]
    msgs = build_rag_messages("  什么是 RAG？ ", chunks)
    assert len(msgs) == 2
    assert msgs[0] == RagMessage(role="system", content=SYSTEM_PROMPT)
    assert msgs[1].role == "user"
    user = msgs[1].content
    assert user.startswith("参考资料：\n")
    assert "[1] source=rag_basics.md score=1.0000 id=rag_basics.md#0" in user
    assert "RAG 三步" in user
    assert "问题：什么是 RAG？" in user
    assert user.endswith("请基于参考资料回答。")


def test_build_rag_messages_no_context() -> None:
    msgs = build_rag_messages("q", [])
    assert "(无相关资料)" in msgs[1].content


def _seeded_collection():
    client = MiniChromaClient()
    col = client.get_or_create_collection("kb")
    n = index_kb_dir(FIX_KB, col)
    assert n >= 3
    return col


def test_retrieve_top_k_and_bad_k() -> None:
    col = _seeded_collection()
    hits = retrieve(col, "RAG Retrieve Augment Generate 检索", k=2)
    assert len(hits) == 2
    assert hits[0].rank == 1
    assert hits[0].source
    assert hits[0].text
    with pytest.raises(RagError, match="k"):
        retrieve(col, "RAG", k=0)
    with pytest.raises(RagError, match="k"):
        retrieve(col, "RAG", k=True)  # type: ignore[arg-type]


def test_run_rag_happy_path() -> None:
    col = _seeded_collection()
    seen: list[list[RagMessage]] = []

    def fake_gen(messages: list[RagMessage]) -> str:
        seen.append(list(messages))
        return "  答案：基于资料  \n"

    result = run_rag(col, "什么是 RAG？", generate_fn=fake_gen, k=2)
    assert isinstance(result, RagAnswer)
    assert result.question == "什么是 RAG？"
    assert result.answer == "答案：基于资料"
    assert len(result.contexts) == 2
    assert len(result.messages) == 2
    assert seen and seen[0][0].role == "system"
    assert "参考资料" in seen[0][1].content


def test_run_rag_generate_errors() -> None:
    col = _seeded_collection()

    def bad_type(_m: list[RagMessage]) -> object:
        return 123

    def empty(_m: list[RagMessage]) -> str:
        return "   "

    with pytest.raises(RagError, match="generate"):
        run_rag(col, "RAG", generate_fn=bad_type)  # type: ignore[arg-type]
    with pytest.raises(RagError, match="empty"):
        run_rag(col, "RAG", generate_fn=empty)


def test_demo_generate_reads_first_chunk() -> None:
    msgs = build_rag_messages(
        "问",
        [RetrievedChunk(1, 0.5, "a.md", "第一行内容\n第二行", "a.md#0")],
    )
    out = demo_generate(msgs)
    assert out.startswith("根据参考资料：")
    assert "第一行内容" in out
