"""Day 1 手工运行入口。"""

from __future__ import annotations

from greeter import greet, greet_many


def main() -> None:
    print(greet("Ada"))
    print(greet("Alan", excited=True))
    print(greet_many(["Ada", "Alan"], excited=False))


if __name__ == "__main__":
    main()
