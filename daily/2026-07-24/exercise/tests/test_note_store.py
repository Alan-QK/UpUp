"""Day 5：笔记存储测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from note_store import Note, NoteNotFoundError, NoteStore


def test_add_and_list(tmp_path: Path) -> None:
    store = NoteStore(tmp_path / "notes.json")
    n1 = store.add("  第一篇  ", " hello ")
    n2 = store.add("第二篇", "world")

    assert n1.id == 1
    assert n1.title == "第一篇"
    assert n1.body == "hello"
    assert n2.id == 2

    notes = store.list_notes()
    assert [n.id for n in notes] == [1, 2]
    assert all(isinstance(n, Note) for n in notes)


def test_add_empty_title_raises(tmp_path: Path) -> None:
    store = NoteStore(tmp_path / "notes.json")
    with pytest.raises(ValueError, match="title must not be empty"):
        store.add("   ", "body")


def test_get_and_not_found(tmp_path: Path) -> None:
    store = NoteStore(tmp_path / "notes.json")
    store.add("a", "b")
    assert store.get(1).title == "a"
    with pytest.raises(NoteNotFoundError):
        store.get(99)


def test_delete(tmp_path: Path) -> None:
    store = NoteStore(tmp_path / "notes.json")
    store.add("a", "b")
    store.add("c", "d")
    store.delete(1)
    assert [n.id for n in store.list_notes()] == [2]
    with pytest.raises(NoteNotFoundError):
        store.delete(1)


def test_search_case_insensitive(tmp_path: Path) -> None:
    store = NoteStore(tmp_path / "notes.json")
    store.add("Agent Loop", "think act")
    store.add("Other", "nope")
    store.add("Tools", "AGENT toolkit")

    hits = store.search("agent")
    assert [n.id for n in hits] == [1, 3]
    assert store.search("   ") == []


def test_persists_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "notes.json"
    NoteStore(path).add("持久化", "仍在")
    reloaded = NoteStore(path)
    assert reloaded.get(1).title == "持久化"
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["next_id"] == 2
    assert raw["notes"][0]["title"] == "持久化"


def test_missing_file_starts_empty(tmp_path: Path) -> None:
    store = NoteStore(tmp_path / "missing.json")
    assert store.list_notes() == []
