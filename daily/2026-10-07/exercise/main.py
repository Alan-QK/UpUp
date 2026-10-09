"""Day 54 手工运行入口：流式事件 Demo。"""

from __future__ import annotations

import argparse

from streaming_events import (
    StreamingRunner,
    build_streaming_demo_agent,
    demo_scripted_chat,
    derive_tool_statuses,
    render_event_timeline,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 54 · 流式事件 Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="跑预设 ScriptedChat Demo（默认）",
    )
    parser.add_argument(
        "--goal",
        type=str,
        default="查一下 alpha，再算 7*3",
        help="用户目标（配合 ScriptedChat，语义展示用）",
    )
    parser.add_argument(
        "--timeline",
        action="store_true",
        help="跑完后打印事件时间线",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=6,
        help="FrameworkAgent.max_steps",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="边跑边打印事件 type（模拟前端订阅）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    agent = build_streaming_demo_agent(max_steps=args.max_steps)
    chat = demo_scripted_chat()

    def _live(event) -> None:  # noqa: ANN001
        extra = ""
        if event.tool_name:
            extra = f" {event.tool_name}"
        if event.status:
            extra += f" → {event.status}"
        print(f"  event: {event.type}{extra}")

    on_event = _live if args.live else None
    bundled = StreamingRunner().run(agent, args.goal, chat, on_event=on_event)
    result = bundled.result
    events = bundled.events

    print(f"goal: {result.goal}")
    print(f"stopped: {result.stopped_reason}")
    print(f"steps: {result.steps}")
    print(f"tools: {', '.join(result.tool_names_used) or '(none)'}")
    print(f"final: {result.final_content}")
    print()
    print("--- tool statuses ---")
    for row in derive_tool_statuses(events):
        print(
            f"  [{row['status']}] {row['name']} ({row['call_id']}) "
            f"content={row['content']!r}"
        )

    print()
    print(render_event_timeline(events))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
