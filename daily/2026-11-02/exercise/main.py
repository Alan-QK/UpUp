"""Day 64 手工试跑入口。"""

from __future__ import annotations

import argparse

from memory_policy import (
    filter_writable,
    render_memory_policy_report,
    run_demo_policy,
)


def cmd_demo() -> None:
    decisions, stats = run_demo_policy()
    print("=== 演示语料决策 ===")
    for d in decisions:
        print(
            f"[{d.action:5}] kind={d.kind:10} c={d.confidence:.2f} "
            f"reason={d.reason:18} | {d.normalized_text}"
        )
    print(
        f"\n统计: total={stats.total} write={stats.write_count} "
        f"skip={stats.skip_count} ask={stats.ask_count}"
    )
    print("可写入：")
    for d in filter_writable(decisions):
        print(f"  - ({d.kind}) {d.normalized_text}")


def cmd_report() -> None:
    decisions, stats = run_demo_policy()
    print(render_memory_policy_report(decisions, stats))


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 64 记忆写入策略 Demo")
    parser.add_argument("--demo", action="store_true", help="打印每条决策")
    parser.add_argument("--report", action="store_true", help="打印 Markdown 报告")
    args = parser.parse_args()

    if args.report:
        cmd_report()
    else:
        cmd_demo()


if __name__ == "__main__":
    main()
