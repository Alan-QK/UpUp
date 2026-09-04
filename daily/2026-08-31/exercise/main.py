"""Day 28 手工运行入口：把示例函数打印成 tool schema。"""

from __future__ import annotations

import argparse
import json
from typing import Literal

from tool_schema import function_to_tool_schema, tools_from_functions


def get_weather(
    city: str,
    unit: Literal["celsius", "fahrenheit"] = "celsius",
    detail: bool = False,
) -> str:
    """查询城市天气。

    Args:
        city: 城市名
        unit: 温度单位
        detail: 是否返回详细预报
    """
    return f"{city}:{unit}:{detail}"


def calculator(expression: str) -> str:
    """声明一个计算器工具（今日只生成 schema，不真正求值）。

    Args:
        expression: 算术表达式字符串
    """
    return expression


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 28 · Function → Tool Schema")
    parser.add_argument(
        "--json",
        action="store_true",
        help="只打印 JSON（默认美化打印）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    tools = tools_from_functions(get_weather, calculator)
    # 再单独展示重命名
    renamed = function_to_tool_schema(get_weather, name="weather_query")
    payload = {"tools": tools, "renamed": renamed}
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    print(text)
    return 0 if args.json or text else 0


if __name__ == "__main__":
    raise SystemExit(main())
