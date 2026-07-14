"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations


def greet(name: str, excited: bool = False) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("name must not be empty")
    message = f"Hello, {cleaned}"
    return f"{message}!" if excited else message


def greet_many(names: list[str], excited: bool = False) -> list[str]:
    return [greet(name, excited=excited) for name in names]
