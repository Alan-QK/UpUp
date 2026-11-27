"""Day 45 手工运行入口：双工具 Agent Demo。"""

from __future__ import annotations

import argparse
import json

from dual_agent import render_agent_markdown, run_dual_agent
from toolkit import dual_toolkit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 45 · Dual Tool Agent")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="默认演示：时间 + 计算（并行双工具）",
    )
    parser.add_argument("--calc", type=str, default="", help="只跑计算类问题")
    parser.add_argument("--time", type=str, default="", help="只跑时间类问题")
    parser.add_argument(
        "--both",
        action="store_true",
        help="固定双工具样例句",
    )
    parser.add_argument("--chat", type=str, default="", help="闲聊（不走工具）")
    parser.add_argument(
        "--json",
        action="store_true",
        help="打印完整 messages JSON",
    )
    parser.add_argument(
        "--tools",
        action="store_true",
        help="打印 dual_toolkit Schema",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.tools:
        print(json.dumps(dual_toolkit(), ensure_ascii=False, indent=2))
        return 0

    if args.calc:
        user = args.calc
    elif args.time:
        user = args.time
    elif args.chat:
        user = args.chat
    elif args.both or args.demo or not any([args.calc, args.time, args.chat]):
        user = "现在 Asia/Shanghai 几点？再帮我算一下 12*(3+4)"
    else:
        user = "现在 Asia/Shanghai 几点？再帮我算一下 12*(3+4)"

    result = run_dual_agent(user)

    if args.json:
        print(json.dumps(result.messages, ensure_ascii=False, indent=2))
    else:
        print(render_agent_markdown(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
