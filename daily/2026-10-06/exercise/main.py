"""Day 53 手工运行入口：业务工具 order_lookup 接入 Demo。"""

from __future__ import annotations

import argparse
import json

from business_tools import build_business_agent, render_extension_checklist
from mini_framework import AgentRunner, ScriptedChat


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
    """查 ORD-1002 → Final。"""
    return ScriptedChat(
        [
            {
                "role": "assistant",
                "content": "先查订单",
                "tool_calls": [
                    _tool_call("c1", "order_lookup", {"order_id": "ORD-1002"})
                ],
            },
            {
                "role": "assistant",
                "content": "订单 ORD-1002 正在处理（processing），合计 59.90 CNY，收货地杭州。",
            },
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 53 · 业务工具接入 Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="跑预设 ScriptedChat Demo（默认）",
    )
    parser.add_argument(
        "--goal",
        type=str,
        default="查一下订单 ORD-1002 的状态",
        help="用户目标（配合 ScriptedChat，语义展示用）",
    )
    parser.add_argument(
        "--checklist",
        action="store_true",
        help="只打印自定义工具接入清单",
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

    if args.checklist:
        print(render_extension_checklist())
        return 0

    agent = build_business_agent(max_steps=args.max_steps)
    chat = demo_scripted_chat()
    result = AgentRunner().run(agent, args.goal, chat)

    print(f"goal: {result.goal}")
    print(f"stopped: {result.stopped_reason}")
    print(f"steps: {result.steps}")
    print(f"tools: {', '.join(result.tool_names_used) or '(none)'}")
    print(f"final: {result.final_content}")
    print()
    print("--- tools on agent ---")
    print(", ".join(agent.registry.names()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
