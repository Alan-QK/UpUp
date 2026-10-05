"""Day 46 手工运行入口：ReAct Agent Loop Demo。"""

from __future__ import annotations

import argparse
import json

from agent_loop import ScriptedChat, render_trace_markdown, run_agent_loop
from tools import loop_toolkit


def _lookup_call(call_id: str, key: str) -> dict:
    return {
        "role": "assistant",
        "content": f"先查 {key}",
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": "lookup",
                    "arguments": json.dumps({"key": key}, ensure_ascii=False),
                },
            }
        ],
    }


def _calc_call(call_id: str, expression: str, thought: str) -> dict:
    return {
        "role": "assistant",
        "content": thought,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": "calculate",
                    "arguments": json.dumps(
                        {"expression": expression}, ensure_ascii=False
                    ),
                },
            }
        ],
    }


def _final(text: str) -> dict:
    return {"role": "assistant", "content": text}


def build_demo_chat() -> ScriptedChat:
    """多步：lookup(alpha)=7 → calculate(7*3)=21 → 最终回答。"""
    return ScriptedChat(
        [
            _lookup_call("call_1", "alpha"),
            _calc_call("call_2", "7*3", "拿到 7，再乘以 3"),
            _final("alpha=7，7*3=21。"),
        ]
    )


def build_direct_chat() -> ScriptedChat:
    return ScriptedChat([_final("这是一道不需要工具的题，直接回答即可。")])


def build_max_steps_chat() -> ScriptedChat:
    """一直要工具，用于演示触顶。"""
    return ScriptedChat(
        [
            _lookup_call("call_a", "alpha"),
            _lookup_call("call_b", "beta"),
            _lookup_call("call_c", "france_capital"),
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 46 · ReAct Agent Loop")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="默认多步 Demo：lookup → calculate → final",
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="无工具，一步最终回答",
    )
    parser.add_argument(
        "--max-steps-demo",
        action="store_true",
        help="强制触顶 max_steps=2",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="打印 Markdown 轨迹（可与其它模式组合；默认也打印）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="打印完整 messages JSON",
    )
    parser.add_argument(
        "--tools",
        action="store_true",
        help="打印 loop_toolkit Schema",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.tools:
        print(json.dumps(loop_toolkit(), ensure_ascii=False, indent=2))
        return 0

    if args.direct:
        goal = "用一句话介绍 ReAct"
        chat = build_direct_chat()
        max_steps = 4
    elif args.max_steps_demo:
        goal = "不停查表（演示触顶）"
        chat = build_max_steps_chat()
        max_steps = 2
    else:
        goal = "查 alpha 的值，再把它乘以 3，告诉我结果"
        chat = build_demo_chat()
        max_steps = 6

    result = run_agent_loop(goal, chat, max_steps=max_steps)

    if args.json:
        print(json.dumps(result.messages, ensure_ascii=False, indent=2))
    else:
        print(render_trace_markdown(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
