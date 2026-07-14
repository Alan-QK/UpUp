"""Day 1 练习：带类型注解的问候模块。

请完成 TODO，使 tests/test_greeter.py 全部通过。
"""

from __future__ import annotations


def greet(name: str, excited: bool = False) -> str:
    """返回一句问候。

    规则：
    - name 去掉首尾空格后不能为空，否则抛出 ValueError("name must not be empty")
    - excited=False → "Hello, {name}"
    - excited=True  → "Hello, {name}!"
    """
    # TODO: 实现这里
    raise NotImplementedError


def greet_many(names: list[str], excited: bool = False) -> list[str]:
    """对多个名字分别调用 greet，返回问候列表。

    注意：保持输入顺序；不要静默跳过空名（应让 greet 抛错）。
    """
    # TODO: 实现这里
    raise NotImplementedError
