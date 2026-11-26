"""Day 41 手工运行入口：打印对照表 / 信号分类 / 示例报告。"""

from __future__ import annotations

import argparse

from agent_vs_chatbot import (
    classify_by_signals,
    default_comparison_rows,
    default_scenarios,
    render_comparison_markdown,
    render_examples_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 41 · Chatbot vs Agent Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="打印对照表 + 示例报告（默认行为）",
    )
    parser.add_argument(
        "--table",
        action="store_true",
        help="只打印 Markdown 对照表",
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="只打印场景示例报告",
    )
    parser.add_argument(
        "--classify",
        action="store_true",
        help="按命令行信号做一次分类",
    )
    parser.add_argument(
        "--tools",
        action="store_true",
        help="classify：needs_tools=True",
    )
    parser.add_argument(
        "--multi-step",
        action="store_true",
        help="classify：needs_multi_step=True",
    )
    parser.add_argument(
        "--side-effects",
        action="store_true",
        help="classify：has_side_effects=True",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # 无显式开关时等同 --demo
    show_all = args.demo or not (args.table or args.examples or args.classify)

    if args.classify:
        kind = classify_by_signals(
            needs_tools=args.tools,
            needs_multi_step=args.multi_step,
            has_side_effects=args.side_effects,
        )
        print("信号分类结果")
        print(f"  needs_tools={args.tools}")
        print(f"  needs_multi_step={args.multi_step}")
        print(f"  has_side_effects={args.side_effects}")
        print(f"  → {kind}")
        if not (show_all or args.table or args.examples):
            return 0
        print()

    if show_all or args.table:
        print("# Chatbot vs Agent 对照表\n")
        print(render_comparison_markdown(default_comparison_rows()))
        if show_all or args.examples:
            print()

    if show_all or args.examples:
        print("# 场景示例\n")
        print(render_examples_report(default_scenarios()))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
