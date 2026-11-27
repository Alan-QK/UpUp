"""Day 32：固定窗口 + overlap 文本切分。"""

from __future__ import annotations

import pytest

from chunker import (
    Chunk,
    ChunkError,
    Document,
    chunk_corpus,
    chunk_document,
    chunk_stats,
    chunk_text,
    validate_chunk_params,
)


def test_validate_chunk_params() -> None:
    validate_chunk_params(10, 0)
    validate_chunk_params(10, 9)

    with pytest.raises(ChunkError, match="chunk_size"):
        validate_chunk_params(0, 0)

    with pytest.raises(ChunkError, match="overlap"):
        validate_chunk_params(10, -1)

    with pytest.raises(ChunkError, match="overlap"):
        validate_chunk_params(10, 10)

    with pytest.raises(ChunkError, match="chunk_size"):
        validate_chunk_params(8, 8)


def test_chunk_text_empty_and_short() -> None:
    assert chunk_text("", chunk_size=10, overlap=2) == []

    text = "hello"
    chunks = chunk_text(text, chunk_size=10, overlap=2, source="a.txt")
    assert len(chunks) == 1
    c = chunks[0]
    assert c == Chunk("a.txt", 0, 0, 5, "hello", 5)


def test_chunk_text_sliding_window() -> None:
    # len=20, size=10, overlap=3 → step=7
    # [0,10), [7,17), [14,20)
    text = "0123456789ABCDEFGHIJ"  # 20 chars
    assert len(text) == 20
    chunks = chunk_text(text, chunk_size=10, overlap=3, source="s")
    assert [c.text for c in chunks] == [
        "0123456789",
        "789ABCDEFG",
        "EFGHIJ",
    ]
    assert [(c.start, c.end) for c in chunks] == [(0, 10), (7, 17), (14, 20)]
    assert [c.index for c in chunks] == [0, 1, 2]
    assert all(c.source == "s" for c in chunks)
    assert all(c.char_count == c.end - c.start == len(c.text) for c in chunks)


def test_chunk_text_zero_overlap() -> None:
    text = "abcdefghij"  # 10
    chunks = chunk_text(text, chunk_size=4, overlap=0, source="z")
    assert [c.text for c in chunks] == ["abcd", "efgh", "ij"]
    assert [(c.start, c.end) for c in chunks] == [(0, 4), (4, 8), (8, 10)]


def test_chunk_text_rejects_bad_params() -> None:
    with pytest.raises(ChunkError, match="chunk_size"):
        chunk_text("abc", chunk_size=0, overlap=0)


def test_chunk_document_and_corpus() -> None:
    d1 = Document("a.txt", "0123456789")  # 10
    d2 = Document("b.txt", "XYZ")
    parts = chunk_document(d1, chunk_size=4, overlap=1)
    assert [p.text for p in parts] == ["0123", "3456", "6789"]
    assert all(p.source == "a.txt" for p in parts)

    all_chunks = chunk_corpus([d1, d2], chunk_size=4, overlap=1)
    assert [c.source for c in all_chunks] == [
        "a.txt",
        "a.txt",
        "a.txt",
        "b.txt",
    ]
    # 各文档 index 独立从 0
    assert [c.index for c in all_chunks] == [0, 1, 2, 0]
    assert all_chunks[-1].text == "XYZ"

    assert chunk_corpus([]) == []


def test_chunk_stats() -> None:
    chunks = [
        Chunk("b.md", 0, 0, 3, "one", 3),
        Chunk("a.md", 0, 0, 5, "hello", 5),
        Chunk("b.md", 1, 2, 6, "four", 4),
    ]
    stats = chunk_stats(chunks)
    assert stats["total_chunks"] == 3
    assert stats["total_chars"] == 12
    assert stats["avg_chunk_size"] == 4.0
    assert stats["by_source"] == {"a.md": 1, "b.md": 2}
    assert stats["sources"] == ["b.md", "a.md"]

    empty = chunk_stats([])
    assert empty["total_chunks"] == 0
    assert empty["total_chars"] == 0
    assert empty["avg_chunk_size"] == 0.0
    assert empty["by_source"] == {}
    assert empty["sources"] == []


def test_exact_multiple_of_step() -> None:
    # len=12, size=6, overlap=0 → 正好两整块
    text = "ABCDEFGHIJKL"
    chunks = chunk_text(text, chunk_size=6, overlap=0)
    assert [c.text for c in chunks] == ["ABCDEF", "GHIJKL"]
    assert chunks[-1].end == 12
