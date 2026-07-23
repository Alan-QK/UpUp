"""Day 4：请为 prompt_utils 补至少 3 个单元测试。

提示：
- 正常路径：输入合法 → 断言返回值
- 边界：刚好等于 max_chars、找不到标签
- 异常：用 pytest.raises(...)

下面留了一个示例测试，帮助你对齐风格。请再补至少 3 个（可删掉示例，但总数 ≥ 3）。
"""

from __future__ import annotations

import pytest

from prompt_utils import extract_tagged_block, normalize_whitespace, truncate


def test_normalize_whitespace_collapses_and_strips() -> None:
    """示例：可保留，也可改写。"""
    assert normalize_whitespace("  hello   world\n") == "hello world"


# TODO 1：为 truncate 写一个「不需要截断」的测试
def test_truncate_TODO_no_cut() -> None:
    raise NotImplementedError("请实现：len(text) <= max_chars 时原样返回")


# TODO 2：为 truncate 写一个「需要截断 + ellipsis」或非法 max_chars 的测试
def test_truncate_TODO_cut_or_invalid() -> None:
    raise NotImplementedError("请实现：截断行为或 max_chars < 1 抛 ValueError")


# TODO 3：为 extract_tagged_block 写一个测试（找到 / 找不到 / 非法 tag 任选）
def test_extract_tagged_block_TODO() -> None:
    raise NotImplementedError("请实现：提取标签块或边界/异常行为")
