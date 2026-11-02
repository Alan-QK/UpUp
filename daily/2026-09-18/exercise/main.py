"""Day 42 手工运行入口：打印工具箱 / JSON / 设计校验。"""

from __future__ import annotations

import argparse
import json

from tool_design import (
    check_design_quality,
    default_toolkit,
    render_toolkit_markdown,
    tools_payload,
    validate_tool_schema,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 42 · Tool Schema Design")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="打印 Markdown 工具箱摘要（默认行为）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="打印可直接用于 Chat Completions 的 tools JSON",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="对 default_toolkit 逐个做结构 + 设计质量校验并打印 OK",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    tools = default_toolkit()

    # 无显式开关时等同 --demo
    show_demo = args.demo or not (args.json or args.validate)

    if args.validate:
        for tool in tools:
            validate_tool_schema(tool)
            check_design_quality(tool)
            name = tool["function"]["name"]
            print(f"OK  {name}")
        if not (show_demo or args.json):
            return 0
        print()

    if args.json:
        print(json.dumps(tools_payload(tools), ensure_ascii=False, indent=2))
        if not show_demo:
            return 0
        print()

    if show_demo:
        print(render_toolkit_markdown(tools))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
