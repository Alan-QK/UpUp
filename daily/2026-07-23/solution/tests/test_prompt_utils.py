"""参考测试：请先自己完成 exercise/tests 再对照。"""

from __future__ import annotations

import pytest

from prompt_utils import extract_tagged_block, normalize_whitespace, truncate


def test_normalize_whitespace_collapses_and_strips() -> None:
    assert normalize_whitespace("  hello   world\n") == "hello world"


def test_normalize_whitespace_tabs_and_newlines() -> None:
    assert normalize_whitespace("a\t\tb\n\nc") == "a b c"


def test_truncate_no_cut_when_short_enough() -> None:
    assert truncate("hello", 5) == "hello"
    assert truncate("hi", 10) == "hi"


def test_truncate_appends_ellipsis() -> None:
    assert truncate("abcdefghijklmnopqrstuvwxyz", 10) == "abcdefg..."


def test_truncate_custom_ellipsis() -> None:
    assert truncate("abcdef", 5, ellipsis="…") == "abcd…"


def test_truncate_ellipsis_longer_than_limit() -> None:
    assert truncate("abcdef", 2, ellipsis="...") == ".."


def test_truncate_invalid_max_chars() -> None:
    with pytest.raises(ValueError, match="max_chars must be >= 1"):
        truncate("hi", 0)


def test_extract_tagged_block_found() -> None:
    text = "前缀 <answer>42</answer> 后缀"
    assert extract_tagged_block(text, "answer") == "42"


def test_extract_tagged_block_case_insensitive_and_multiline() -> None:
    text = "<Answer>\nline1\nline2\n</ANSWER>"
    assert extract_tagged_block(text, "answer") == "\nline1\nline2\n"


def test_extract_tagged_block_missing() -> None:
    assert extract_tagged_block("no tags here", "answer") is None


def test_extract_tagged_block_invalid_tag() -> None:
    with pytest.raises(ValueError, match="tag must be a non-empty token"):
        extract_tagged_block("<a>1</a>", "  ")
    with pytest.raises(ValueError, match="tag must be a non-empty token"):
        extract_tagged_block("<a>1</a>", "bad tag")
