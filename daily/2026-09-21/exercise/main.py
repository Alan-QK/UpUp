"""Day 43 手工运行入口：演示单轮 tool call 执行。"""

from __future__ import annotations

import argparse
import json

from tool_executor import (
    execute_assistant_tool_calls,
    render_results_markdown,
    to_tool_messages,
)


def _success_message() -> dict:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_weather_1",
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"city": "Shanghai", "unit": "celsius"}',
                },
            },
            {
                "id": "call_calc_1",
                "type": "function",
                "function": {
                    "name": "calculate",
                    "arguments": '{"expression": "12 * (3 + 4)"}',
                },
            },
            {
                "id": "call_time_1",
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "arguments": '{"timezone": "Asia/Shanghai"}',
                },
            },
        ],
    }


def _fail_message() -> dict:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_bad_1",
                "type": "function",
                "function": {
                    "name": "launch_missile",
                    "arguments": "{}",
                },
            },
            {
                "id": "call_bad_2",
                "type": "function",
                "function": {
                    "name": "calculate",
                    "arguments": '{"expression": "__import__(\\"os\\").system(\\"ls\\")"}',
                },
            },
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 43 · Tool Call Executor")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="执行三条成功工具调用并打印 Markdown（默认行为）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="打印 role=tool 回填消息 JSON",
    )
    parser.add_argument(
        "--fail",
        action="store_true",
        help="演示未知工具与不安全表达式的失败回传",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    show_demo = args.demo or not (args.json or args.fail)

    if args.fail:
        message = _fail_message()
    else:
        message = _success_message()

    results = execute_assistant_tool_calls(message)

    if args.json:
        print(json.dumps(to_tool_messages(results), ensure_ascii=False, indent=2))
    elif show_demo or args.fail:
        print(render_results_markdown(results))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
