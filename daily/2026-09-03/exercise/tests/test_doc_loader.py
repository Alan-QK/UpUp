"""Day 31：文档加载与清洗 · txt/md loader。"""

from __future__ import annotations

from pathlib import Path

import pytest

from doc_loader import (
    SUPPORTED_SUFFIXES,
    DocLoadError,
    Document,
    clean_text,
    collapse_blank_lines,
    corpus_stats,
    discover_documents,
    is_supported_file,
    load_corpus,
    load_document,
    normalize_newlines,
    read_text_file,
    strip_bom,
    strip_html_comments,
    strip_yaml_frontmatter,
)

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_strip_bom_and_newlines() -> None:
    assert strip_bom("hello") == "hello"
    assert strip_bom("\ufeffhello") == "hello"
    assert normalize_newlines("a\r\nb\rc") == "a\nb\nc"


def test_collapse_blank_lines() -> None:
    raw = "a  \n\n\n\nb\t\n\nc"
    out = collapse_blank_lines(raw, max_consecutive=2)
    assert out == "a\n\n\nb\n\nc\n"

    single = collapse_blank_lines("x\n\n\n\ny", max_consecutive=1)
    assert single == "x\n\ny\n"

    assert collapse_blank_lines("   \n\n  ") == ""

    with pytest.raises(DocLoadError, match="max_consecutive"):
        collapse_blank_lines("a", max_consecutive=0)


def test_strip_frontmatter_and_comments() -> None:
    md = "---\ntitle: hi\n---\n\n# Body\n"
    assert strip_yaml_frontmatter(md) == "\n# Body\n"

    no_close = "---\ntitle: hi\n# Body\n"
    assert strip_yaml_frontmatter(no_close) == no_close

    plain = "# No frontmatter\n"
    assert strip_yaml_frontmatter(plain) == plain

    commented = "A <!-- hide\nme --> B <!--x--> C"
    assert strip_html_comments(commented) == "A  B  C"


def test_clean_text_pipeline() -> None:
    raw = (
        "\ufeff---\ntitle: t\n---\r\n"
        "# Hello  \r\n\r\n\r\n"
        "<!-- note -->World\r\n"
    )
    cleaned = clean_text(raw)
    # 输入含 2 个连续空行，max_blank_lines=2 → 保留两行空行（\n\n\n）
    assert cleaned == "# Hello\n\n\nWorld\n"
    assert "title:" not in cleaned
    assert "note" not in cleaned

    keep_meta = clean_text(raw, strip_frontmatter=False, strip_comments=False)
    assert "title: t" in keep_meta
    assert "note" in keep_meta


def test_read_and_is_supported(tmp_path: Path) -> None:
    f = tmp_path / "a.md"
    f.write_text("你好", encoding="utf-8")
    assert read_text_file(f) == "你好"
    assert is_supported_file(f) is True
    assert is_supported_file(tmp_path / "x.py") is False
    assert is_supported_file(tmp_path) is False

    with pytest.raises(DocLoadError, match="not a file"):
        read_text_file(tmp_path / "missing.txt")

    bad = tmp_path / "bad.txt"
    bad.write_bytes(b"\xff\xfe\x00\x01")
    with pytest.raises(DocLoadError, match="utf-8"):
        read_text_file(bad)


def test_discover_skips_hidden(tmp_path: Path) -> None:
    (tmp_path / "ok.txt").write_text("a", encoding="utf-8")
    (tmp_path / ".secret.md").write_text("no", encoding="utf-8")
    hidden_dir = tmp_path / ".hidden"
    hidden_dir.mkdir()
    (hidden_dir / "x.md").write_text("no", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.markdown").write_text("b", encoding="utf-8")
    (sub / "c.py").write_text("c", encoding="utf-8")

    found = discover_documents(tmp_path)
    rels = [p.relative_to(tmp_path).as_posix() for p in found]
    assert rels == ["ok.txt", "sub/b.markdown"]

    with pytest.raises(DocLoadError, match="not a directory"):
        discover_documents(tmp_path / "ok.txt")


def test_load_document_and_corpus() -> None:
    docs = load_corpus(FIXTURES)
    sources = [d.source for d in docs]
    assert sources == ["leave.txt", "nested/guide.markdown", "note.md"]

    note = next(d for d in docs if d.source == "note.md")
    assert note.suffix == ".md"
    assert "报销指南" in note.text
    assert "title:" not in note.text
    assert "编辑备注" not in note.text
    assert note.char_count < note.raw_char_count
    assert note.text.endswith("\n")

    leave = load_document(FIXTURES / "leave.txt", root=FIXTURES)
    assert leave.source == "leave.txt"
    assert leave.suffix == ".txt"
    assert "年假" in leave.text

    alone = load_document(FIXTURES / "leave.txt")
    assert alone.source == "leave.txt"

    assert load_corpus(FIXTURES / "nested")  # non-empty
    empty = FIXTURES / "nested"
    # nested only has guide.markdown — already covered


def test_corpus_stats() -> None:
    docs = [
        Document("a.txt", "hi\n", ".txt", 10, 3),
        Document("b.md", "hello\n", ".md", 20, 6),
        Document("c.md", "x\n", ".md", 5, 2),
    ]
    stats = corpus_stats(docs)
    assert stats["total_docs"] == 3
    assert stats["total_chars"] == 11
    assert stats["total_raw_chars"] == 35
    assert stats["by_suffix"] == {".md": 2, ".txt": 1}
    assert stats["sources"] == ["a.txt", "b.md", "c.md"]

    empty_stats = corpus_stats([])
    assert empty_stats["total_docs"] == 0
    assert empty_stats["by_suffix"] == {}
    assert empty_stats["sources"] == []


def test_supported_suffixes_constant() -> None:
    assert SUPPORTED_SUFFIXES == (".txt", ".md", ".markdown")
