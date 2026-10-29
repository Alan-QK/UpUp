"""Day 44 手工运行入口：演示工具结果回填后再问模型。"""

from __future__ import annotations

import argparse
import json

from mini_executor import to_tool_messages, execute_assistant_tool_calls
from roundtrip import (
    RoundTripResult,
    ScriptedChat,
    render_roundtrip_markdown,
    run_tool_roundtrip,
    validate_tool_followup,
)


def _user_history() -> list[dict]:
    return [
        {
            "role": "user",
            "content": "上海天气怎么样？顺便把 28*9/5+32 算一下。",
        }
    ]


def _assistant_with_tools() -> dict:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_weather",
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"city": "Shanghai", "unit": "celsius"}',
                },
            },
            {
                "id": "call_calc",
                "type": "function",
                "function": {
                    "name": "calculate",
                    "arguments": '{"expression": "28*9/5+32"}',
                },
            },
        ],
    }


def _final_answer() -> dict:
    return {
        "role": "assistant",
        "content": "上海今天约 28°C、晴。按你的公式换算大约 82.4°F。",
    }


def _plain_answer() -> dict:
    return {
        "role": "assistant",
        "content": "这是一道心算题，答案是 4。",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 44 · Tool Result Roundtrip")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="完整一轮：tool_calls → 执行 → 回填 → 最终回答（默认）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="打印最终 messages JSON",
    )
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="第一轮直接给最终回答（不走工具）",
    )
    parser.add_argument(
        "--mismatch",
        action="store_true",
        help="演示 tool_call_id 对不上时的校验失败",
    )
    return parser


def _run_demo(*, use_tools: bool) -> RoundTripResult:
    history = _user_history()
    if use_tools:
        chat = ScriptedChat([_assistant_with_tools(), _final_answer()])
    else:
        chat = ScriptedChat([_plain_answer()])
    return run_tool_roundtrip(history, chat)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    show_demo = args.demo or not (args.json or args.no_tools or args.mismatch)

    if args.mismatch:
        assistant = _assistant_with_tools()
        bad_tools = [
            {
                "role": "tool",
                "tool_call_id": "call_WRONG",
                "content": "{}",
            },
            {
                "role": "tool",
                "tool_call_id": "call_calc",
                "content": "{}",
            },
        ]
        try:
            validate_tool_followup(assistant, bad_tools)
        except ValueError as exc:
            print(f"expected validation error: {exc}")
            return 0
        print("ERROR: mismatch was not detected")
        return 1

    result = _run_demo(use_tools=not args.no_tools)

    if args.json:
        print(json.dumps(result.messages, ensure_ascii=False, indent=2))
    elif show_demo or args.no_tools:
        print(render_roundtrip_markdown(result))
        # 额外打印第一轮执行摘要，方便对照 Day 43
        if result.used_tools:
            print("\n# Executor peek")
            peek = execute_assistant_tool_calls(_assistant_with_tools())
            print(json.dumps(to_tool_messages(peek), ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
