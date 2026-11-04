"""Day 48 手工运行入口：工具错误恢复 Demo。"""

from __future__ import annotations

import argparse
import json

from error_recovery import (
    RecoveryPolicy,
    ScriptedChat,
    render_trace_markdown,
    run_recovery_loop,
)
from tools import loop_toolkit


def _calc(call_id: str, expression: str | None, thought: str = "") -> dict:
    if expression is None:
        args: dict | str = {}
    else:
        args = {"expression": expression}
    return {
        "role": "assistant",
        "content": thought or ("计算" if expression else "少参数"),
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": "calculate",
                    "arguments": json.dumps(args, ensure_ascii=False),
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
    """缺 expression → 纠正 → 最终回答。"""
    return ScriptedChat(
        [
            _calc("bad", None, "先算一下（漏了参数）"),
            _calc("ok", "7*3", "补上 expression"),
            _final("7×3 = 21。"),
        ]
    )


def build_lookup_chat() -> ScriptedChat:
    return ScriptedChat(
        [
            _lookup("m1", "gamma", "错键"),
            _lookup("m2", "alpha", "改成 alpha"),
            _final("alpha 的值是 7。"),
        ]
    )


def build_fail_chat() -> ScriptedChat:
    return ScriptedChat(
        [
            _lookup("a", "nope1"),
            _lookup("b", "nope2"),
            _lookup("c", "nope3"),
            _final("不该出现"),
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 48 · 工具错误恢复")
    parser.add_argument("--demo", action="store_true", help="缺参 → 纠正 → final")
    parser.add_argument("--lookup", action="store_true", help="未知键 → 纠正 → final")
    parser.add_argument(
        "--fail",
        action="store_true",
        help="连续 ERROR 触顶 too_many_errors",
    )
    parser.add_argument("--trace", action="store_true", help="打印轨迹（默认也会）")
    parser.add_argument("--json", action="store_true", help="打印 messages JSON")
    parser.add_argument("--tools", action="store_true", help="打印 toolkit Schema")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.tools:
        print(json.dumps(loop_toolkit(), ensure_ascii=False, indent=2))
        return 0

    if args.lookup:
        goal = "查 alpha 的值"
        chat = build_lookup_chat()
        policy = RecoveryPolicy()
    elif args.fail:
        goal = "演示连续错误熔断"
        chat = build_fail_chat()
        policy = RecoveryPolicy(max_steps=6, max_consecutive_errors=3)
    else:
        goal = "算 7*3"
        chat = build_demo_chat()
        policy = RecoveryPolicy()

    result = run_recovery_loop(goal, chat, policy=policy)

    if args.json:
        print(json.dumps(result.messages, ensure_ascii=False, indent=2))
    else:
        print(render_trace_markdown(result))
        print(f"\nrecovery_count={result.recovery_count}")
        print(f"consecutive_error_streak={result.consecutive_error_streak}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
