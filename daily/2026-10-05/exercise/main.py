"""Day 52 手工运行入口：迷你框架版 lookup+calculate Agent Demo。"""

from __future__ import annotations

import argparse
import json

from mini_framework import (
    AgentRunner,
    ScriptedChat,
    build_default_agent,
    render_mapping_markdown,
)


def _tool_call(call_id: str, name: str, arguments: dict) -> dict:
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(arguments, ensure_ascii=False),
        },
    }


def demo_scripted_chat() -> ScriptedChat:
    """多步：lookup alpha → calculate 7*3 → final。"""
    return ScriptedChat(
        [
            {
                "role": "assistant",
                "content": "先查 alpha",
                "tool_calls": [_tool_call("c1", "lookup", {"key": "alpha"})],
            },
            {
                "role": "assistant",
                "content": "再算 7*3",
                "tool_calls": [
                    _tool_call("c2", "calculate", {"expression": "7*3"})
                ],
            },
            {
                "role": "assistant",
                "content": "alpha 为 7，乘以 3 得到 21。",
            },
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 52 · 迷你框架 Agent Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="跑预设多步 ScriptedChat Demo（默认）",
    )
    parser.add_argument(
        "--goal",
        type=str,
        default="查 alpha 的值，再把它乘以 3",
        help="用户目标（配合 ScriptedChat，语义展示用）",
    )
    parser.add_argument(
        "--mapping",
        action="store_true",
        help="只打印手写↔框架对照表",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=6,
        help="FrameworkAgent.max_steps",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.mapping:
        print(render_mapping_markdown())
        return 0

    agent = build_default_agent(max_steps=args.max_steps)
    chat = demo_scripted_chat()
    result = AgentRunner().run(agent, args.goal, chat)

    print(f"goal: {result.goal}")
    print(f"stopped: {result.stopped_reason}")
    print(f"steps: {result.steps}")
    print(f"tools: {', '.join(result.tool_names_used) or '(none)'}")
    print(f"final: {result.final_content}")
    print()
    print("--- mapping ---")
    print(render_mapping_markdown())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
