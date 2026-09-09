"""Day 35：本地笔记检索 · 加载/切分/索引/top-k CLI。"""

from __future__ import annotations

from pathlib import Path

import pytest

from notes_search import (
    Chunk,
    IndexReport,
    NoteDoc,
    NotesSearchError,
    SearchHit,
    chunk_note,
    chunk_text,
    discover_notes,
    fake_embed,
    format_hits,
    index_documents,
    index_notes_dir,
    load_note,
    make_chunk_id,
    search_notes,
    validate_chunk_params,
)
from vector_store import MiniChromaClient, MiniCollection


FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "notes"


def test_discover_notes_skips_hidden_and_sorts() -> None:
    paths = discover_notes(FIXTURES)
    rels = [p.relative_to(FIXTURES).as_posix() for p in paths]
    assert rels == ["chroma.md", "frontend.md", "python.txt", "rag.md"]
    assert all(p.is_absolute() for p in paths)

    with pytest.raises(NotesSearchError, match="not a directory"):
        discover_notes(FIXTURES / "rag.md")


def test_load_note_and_empty() -> None:
    doc = load_note(FIXTURES / "rag.md", root=FIXTURES)
    assert doc.source == "rag.md"
    assert "RAG" in doc.text
    assert "\r" not in doc.text

    with pytest.raises(NotesSearchError, match="not a file"):
        load_note(FIXTURES / "missing.md", root=FIXTURES)


def test_chunk_text_overlap_and_validate() -> None:
    validate_chunk_params(10, 2)
    with pytest.raises(NotesSearchError, match="chunk_size"):
        validate_chunk_params(0, 0)
    with pytest.raises(NotesSearchError, match="overlap"):
        validate_chunk_params(10, -1)
    with pytest.raises(NotesSearchError, match="overlap"):
        validate_chunk_params(10, 10)

    assert chunk_text("") == []
    text = "abcdefghij"  # 10
    chunks = chunk_text(text, chunk_size=4, overlap=1, source="t.md")
    assert [c.text for c in chunks] == ["abcd", "defg", "ghij"]
    assert chunks[0].start == 0 and chunks[0].end == 4
    assert chunks[-1].end == 10
    assert chunks[1].index == 1
    assert all(isinstance(c, Chunk) for c in chunks)

    doc = NoteDoc(source="t.md", text=text)
    assert [c.text for c in chunk_note(doc, chunk_size=4, overlap=1)] == [
        "abcd",
        "defg",
        "ghij",
    ]


def test_make_chunk_id() -> None:
    assert make_chunk_id("rag.md", 0) == "rag.md#0"
    assert make_chunk_id("a/b.md", 2) == "a/b.md#2"


def test_index_documents_and_search_topk() -> None:
    col = MiniCollection("notes")
    docs = [
        NoteDoc("a.md", "RAG 检索与向量 top-k"),
        NoteDoc("b.md", "今天天气适合散步"),
        NoteDoc("c.md", "Chroma Collection add query"),
    ]
    report = index_documents(docs, col, chunk_size=80, overlap=10)
    assert isinstance(report, IndexReport)
    assert report.files == 3
    assert report.chunks >= 3
    assert report.skipped_empty == 0
    assert col.count() == report.chunks

    hits = search_notes(col, "如何做向量检索 top-k", k=2)
    assert len(hits) == 2
    assert hits[0].rank == 1
    assert hits[0].score >= hits[1].score
    assert "rag" in hits[0].source or "RAG" in hits[0].text or "检索" in hits[0].text
    assert isinstance(hits[0], SearchHit)


def test_index_validations() -> None:
    col = MiniCollection("x")
    with pytest.raises(NotesSearchError, match="empty"):
        index_documents([], col)

    with pytest.raises(NotesSearchError, match="no chunks"):
        index_documents([NoteDoc("e.md", "")], col, chunk_size=10, overlap=2)


def test_search_validations_and_format() -> None:
    col = MiniCollection("s")
    index_documents(
        [NoteDoc("p.md", "Python pytest dataclass pathlib")],
        col,
        chunk_size=100,
        overlap=10,
    )

    with pytest.raises(NotesSearchError, match="query"):
        search_notes(col, "   ")
    with pytest.raises(NotesSearchError, match="k"):
        search_notes(col, "python", k=0)
    with pytest.raises(NotesSearchError, match="k"):
        search_notes(col, "python", k=True)  # type: ignore[arg-type]

    hits = search_notes(col, "pytest 与 dataclass", k=1)
    text = format_hits(hits, query="pytest 与 dataclass")
    assert text.startswith("query: pytest 与 dataclass\n")
    assert f"#{hits[0].rank}" in text
    assert f"score={hits[0].score:.4f}" in text
    assert f"source={hits[0].source}#{hits[0].chunk_index}" in text
    assert f"id={hits[0].id}" in text
    assert hits[0].text in text

    assert format_hits([], query="") == "query: (empty)\nno hits"


def test_index_notes_dir_end_to_end() -> None:
    client = MiniChromaClient()
    col = client.get_or_create_collection("local-notes")
    report = index_notes_dir(FIXTURES, col, chunk_size=90, overlap=15)
    assert report.files == 4
    assert report.chunks >= 4
    assert col.count() == report.chunks

    hits = search_notes(col, "前端 SSE 流式与引用", k=2)
    assert len(hits) >= 1
    assert hits[0].source in {"frontend.md", "rag.md", "chroma.md", "python.txt"}

    # 隐藏文件未入库
    ids = []
    # ponytail: O(n) scan of collection via query dump; fine for fixture-sized demos
    dump = col.query(
        query_embeddings=[fake_embed("anything")],
        n_results=max(col.count(), 1),
    )[0]
    for m in dump:
        ids.append(m.id)
        assert not str(m.metadata.get("source", "")).startswith(".")

    rendered = format_hits(hits, query="前端 SSE 流式与引用")
    assert "query: 前端 SSE 流式与引用" in rendered
    assert f"#{hits[0].rank}" in rendered


def test_fake_embed_deterministic() -> None:
    a = fake_embed("hello RAG")
    b = fake_embed("hello RAG")
    assert a == b
    assert len(a) == 16
