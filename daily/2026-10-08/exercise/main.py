"""Day 55 手工运行入口：按目标打印手写 vs 框架对比摘要 / 完整报告。"""

from __future__ import annotations

import argparse

from comparison_report import (
    APPROACH_FRAMEWORK,
    APPROACH_HANDWRITTEN,
    GOAL_INTERVIEW,
    GOAL_LEARN_LOOP,
    GOAL_ONBOARD,
    GOAL_SHIP_PRODUCT,
    recommend_for_goal,
    recommendation_reason,
    render_comparison_report,
    summarize_side_wins,
    week11_default_scores,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 55 · 手写 vs 框架对比 Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="打印四周目标的推荐摘要（默认行为）",
    )
    parser.add_argument(
        "--goal",
        choices=[
            GOAL_LEARN_LOOP,
            GOAL_SHIP_PRODUCT,
            GOAL_INTERVIEW,
            GOAL_ONBOARD,
        ],
        help="指定单个目标并打印推荐",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="输出完整 Markdown 对比报告（需配合 --goal，缺省 goal=learn_loop）",
    )
    return parser


def print_goal_summary(goal: str) -> None:
    winner = recommend_for_goal(goal)
    label = "手写" if winner == APPROACH_HANDWRITTEN else "框架"
    print(f"[{goal}] 主选 → {winner}（{label}）")
    print(f"  理由：{recommendation_reason(goal)}")


def print_demo() -> None:
    scores = week11_default_scores()
    wins = summarize_side_wins(scores)
    print("=== Week 11 默认维度胜负 ===")
    print(f"手写领先：{', '.join(wins.handwritten) or '（无）'}")
    print(f"框架领先：{', '.join(wins.framework) or '（无）'}")
    print(f"平局：{', '.join(wins.ties) or '（无）'}")
    print()
    print("=== 按目标推荐 ===")
    for goal in (
        GOAL_LEARN_LOOP,
        GOAL_INTERVIEW,
        GOAL_SHIP_PRODUCT,
        GOAL_ONBOARD,
    ):
        print_goal_summary(goal)
        print()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.report:
        goal = args.goal or GOAL_LEARN_LOOP
        print(render_comparison_report(goal))
        return 0

    if args.goal:
        print_goal_summary(args.goal)
        return 0

    # --demo 或无参数：摘要
    print_demo()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
