"""Day 49 手工运行入口：轨迹日志 Trace Demo。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools import loop_toolkit
from trace_log import (
    ScriptedChat,
    TracePolicy,
    dump_trace_jsonl,
    load_trace_jsonl,
    render_trace_text,
    run_traced_loop,
)


def _calc(call_id: str, expression: str, thought: str = "") -> dict:
    return {
        "role": "assistant",
        "content": thought or f"计算 {expression}",
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


def _lookup(call_id: str, key: str, thought: str = "") -> dict:
    return {
        "role": "assistant",
        "content": thought or f"查 {key}",
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


def _final(text: str) -> dict:
    return {"role": "assistant", "content": text}


def build_demo_chat() -> ScriptedChat:
    """单工具 → final。"""
    return ScriptedChat(
        [
            _lookup("c1", "alpha", "先查 alpha"),
            _final("alpha 的值是 7。"),
        ]
    )


def build_multi_chat() -> ScriptedChat:
    """lookup → calculate → final。"""
    return ScriptedChat(
        [
            _lookup("c1", "alpha", "先取 alpha"),
            _calc("c2", "7*3", "再用 7*3 验证"),
            _final("alpha=7，且 7×3=21。"),
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 49 · 轨迹日志 Trace")
    parser.add_argument("--demo", action="store_true", help="单步 lookup → final")
    parser.add_argument("--multi", action="store_true", help="多步 lookup+calculate")
    parser.add_argument(
        "--jsonl",
        type=str,
        default="",
        help="把轨迹写入指定 JSONL 路径",
    )
    parser.add_argument(
        "--replay",
        type=str,
        default="",
        help="从 JSONL 回放并打印文本轨迹",
    )
    parser.add_argument("--quiet", action="store_true", help="关闭 live_print")
    parser.add_argument("--tools", action="store_true", help="打印 toolkit Schema")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.tools:
        print(json.dumps(loop_toolkit(), ensure_ascii=False, indent=2))
        return 0

    if args.replay:
        trace = load_trace_jsonl(Path(args.replay))
        print(render_trace_text(trace))
        return 0

    if args.multi:
        goal = "查 alpha 并验证 7*3"
        chat = build_multi_chat()
    else:
        goal = "查 alpha 的值"
        chat = build_demo_chat()

    policy = TracePolicy(max_steps=6, live_print=not args.quiet)
    result = run_traced_loop(goal, chat, policy=policy)

    print()
    print(render_trace_text(result))

    if args.jsonl:
        dump_trace_jsonl(args.jsonl, result)
        print(f"\nJSONL written: {args.jsonl}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
