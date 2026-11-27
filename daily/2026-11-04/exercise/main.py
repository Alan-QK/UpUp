"""Day 66 入口：任务分解 Planner 演示。"""

from __future__ import annotations

import argparse

from planner import (
    plan_from_goal,
    render_plan,
    render_planner_report,
    run_demo_planner,
    summarize_plans,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 66 · 任务分解 Planner")
    parser.add_argument(
        "--goal",
        type=str,
        default="",
        help="单个目标；省略则跑演示集",
    )
    parser.add_argument("--demo", action="store_true", help="批量演示规划")
    parser.add_argument("--report", action="store_true", help="输出学习报告")
    parser.add_argument(
        "--max-steps",
        type=int,
        default=8,
        help="最大步骤数（3–12）",
    )
    args = parser.parse_args()

    if args.report:
        print(render_planner_report())
        return

    if args.goal.strip():
        plan = plan_from_goal(args.goal, max_steps=args.max_steps)
        print(render_plan(plan))
        return

    # 默认 / --demo：批量
    plans = run_demo_planner()
    stats = summarize_plans(plans)
    print(f"成功规划 {stats['plan_count']} 个目标，共 {stats['total_steps']} 步")
    print(f"分类分布：{stats['by_kind']}")
    print(f"复杂度分布：{stats['by_complexity']}")
    print()
    if plans:
        print(render_plan(plans[0]))


if __name__ == "__main__":
    main()
