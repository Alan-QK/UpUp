"""Day 62 手工试跑入口。"""

from __future__ import annotations

import argparse

from summary_memory import (
    SummarizingMemory,
    build_demo_exchanges,
    compact_exchanges,
    is_summary_message,
    render_summary_report,
)


def _print_messages(messages: list) -> None:
    for m in messages:
        mark = " 📝" if is_summary_message(m) else ""
        print(f"[{m.role}]{mark} {m.content}")


def cmd_demo() -> None:
    exchanges = build_demo_exchanges()
    print("=== 原始 5 轮 ===")
    for i, (u, a) in enumerate(exchanges, 1):
        print(f"{i}. U: {u}")
        print(f"   A: {a}")

    result = compact_exchanges(
        exchanges,
        keep_recent_turns=2,
        system_prompt="前端转 Agent 学习助理",
    )
    print("\n=== keep_recent_turns=2 压缩后 ===")
    _print_messages(result.messages)
    print(
        f"\nstats: folded={result.stats.folded_exchanges} "
        f"kept={result.stats.kept_recent_exchanges} "
        f"tokens≈{result.stats.estimated_tokens_context}"
    )


def cmd_roll() -> None:
    print("=== SummarizingMemory 滚动追加 ===")
    mem = SummarizingMemory(keep_recent_turns=2, system_prompt="学习助理")
    for user, assistant in build_demo_exchanges():
        result = mem.add_exchange(user, assistant)
        print(
            f"+ ({user[:12]}…) → folded={result.stats.folded_exchanges} "
            f"recent={len(mem.exchanges())} "
            f"summary_chars={len(mem.summary or '')}"
        )
    print("\n最终上下文：")
    _print_messages(mem.context_messages())


def cmd_report() -> None:
    result = compact_exchanges(
        build_demo_exchanges(),
        keep_recent_turns=2,
        system_prompt="学习助理",
    )
    print(render_summary_report(result))


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 62 摘要记忆 Demo")
    parser.add_argument("--demo", action="store_true", help="一次性压缩演示")
    parser.add_argument("--roll", action="store_true", help="滚动会话记忆演示")
    parser.add_argument("--report", action="store_true", help="打印 Markdown 报告")
    args = parser.parse_args()

    if args.report:
        cmd_report()
    elif args.roll:
        cmd_roll()
    else:
        cmd_demo()


if __name__ == "__main__":
    main()
