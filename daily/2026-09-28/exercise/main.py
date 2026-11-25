"""Day 47 手工运行入口：StopPolicy 守卫 Loop Demo。"""

from __future__ import annotations

import argparse
import json

from stop_guard import ScriptedChat, StopPolicy, render_trace_markdown, run_guarded_loop
from tools import loop_toolkit


def _lookup_call(call_id: str, key: str, thought: str = "") -> dict:
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
    return ScriptedChat(
        [
            _lookup_call("call_1", "alpha"),
            _final("alpha 的值是 7。"),
        ]
    )


def build_repeat_chat() -> ScriptedChat:
    return ScriptedChat(
        [
            _lookup_call("r1", "alpha", "再查一遍"),
            _lookup_call("r2", "alpha", "还是这个"),
            _lookup_call("r3", "alpha", "继续"),
            _final("不该出现"),
        ]
    )


def build_last_step_chat() -> ScriptedChat:
    return ScriptedChat(
        [
            _lookup_call("a", "alpha"),
            _lookup_call("b", "beta"),
        ]
    )


def build_max_steps_chat() -> ScriptedChat:
    return ScriptedChat(
        [
            _lookup_call("a", "alpha"),
            _lookup_call("b", "beta"),
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 47 · StopPolicy 守卫 Loop")
    parser.add_argument("--demo", action="store_true", help="正常：lookup → final")
    parser.add_argument("--repeat", action="store_true", help="重复同一 lookup，触发熔断")
    parser.add_argument(
        "--last-step",
        action="store_true",
        help="max_steps=2 且最后一步拦截工具",
    )
    parser.add_argument(
        "--max-steps",
        action="store_true",
        help="关闭 last-step 拦截，演示跑满 max_steps",
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

    if args.repeat:
        goal = "演示重复动作熔断"
        chat = build_repeat_chat()
        policy = StopPolicy(max_steps=6, max_identical_streak=2)
    elif args.last_step:
        goal = "演示最后一步拦截工具"
        chat = build_last_step_chat()
        policy = StopPolicy(max_steps=2, max_identical_streak=5, block_tools_on_last_step=True)
    elif args.max_steps:
        goal = "演示跑满步数（允许最后一步执行工具）"
        chat = build_max_steps_chat()
        policy = StopPolicy(max_steps=2, max_identical_streak=5, block_tools_on_last_step=False)
    else:
        goal = "查 alpha 的值"
        chat = build_demo_chat()
        policy = StopPolicy()

    result = run_guarded_loop(goal, chat, policy=policy)

    if args.json:
        print(json.dumps(result.messages, ensure_ascii=False, indent=2))
    else:
        print(render_trace_markdown(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
