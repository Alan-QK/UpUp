"""Day 71 入口：多智能体适用性决策演示。"""

from __future__ import annotations

import argparse

from multiagent_decision import (
    build_demo_decisions,
    render_checklist,
    render_decision_report,
    summarize_decision,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 71 · 何时用多智能体")
    parser.add_argument("--demo", action="store_true", help="批量演示六条场景")
    parser.add_argument("--report", action="store_true", help="输出学习报告")
    parser.add_argument(
        "--checklist",
        action="store_true",
        help="打印每条场景的完整清单",
    )
    args = parser.parse_args()

    decisions = build_demo_decisions()

    if args.report:
        print(render_decision_report(decisions))
        return

    if args.checklist:
        for d in decisions:
            print(render_checklist(d))
            print("-" * 40)
        return

    # 默认 / --demo：一行摘要
    print(f"演示 {len(decisions)} 条多智能体决策")
    for d in decisions:
        sm = summarize_decision(d)
        print(
            f"- {sm['recommendation']}: score={sm['score']} "
            f"pro={sm['pro_count']} con={sm['con_count']} | {sm['title']}"
        )


if __name__ == "__main__":
    main()
