"""Day 1 greeter 单元测试。"""

from __future__ import annotations

import pytest

from greeter import greet, greet_many


def test_greet_basic() -> None:
    assert greet("Ada") == "Hello, Ada"


def test_greet_excited() -> None:
    assert greet("Ada", excited=True) == "Hello, Ada!"


def test_greet_strips_whitespace() -> None:
    assert greet("  Ada  ") == "Hello, Ada"


def test_greet_empty_name_raises() -> None:
    with pytest.raises(ValueError, match="name must not be empty"):
        greet("   ")


def test_greet_many_preserves_order() -> None:
    assert greet_many(["Ada", "Alan"]) == ["Hello, Ada", "Hello, Alan"]
