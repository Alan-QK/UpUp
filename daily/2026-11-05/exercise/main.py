"""Day 67 入口：Plan-and-Execute 执行器演示。"""

from __future__ import annotations

import argparse

from executor import (
    build_sample_plan,
    default_tool_registry,
    execute_plan,
    render_execution,
    render_executor_report,
    run_demo_executor,
    summarize_execution,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 67 · Plan-and-Execute")
    parser.add_argument(
        "--goal",
        type=str,
        default="",
        help="单个目标（用内置 sample plan 模板执行）",
    )
    parser.add_argument("--demo", action="store_true", help="批量演示执行")
    parser.add_argument("--report", action="store_true", help="输出学习报告")
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="最多实际调用工具次数",
    )
    args = parser.parse_args()

    if args.report:
        print(render_executor_report())
        return

    if args.goal.strip():
        plan = build_sample_plan(goal=args.goal.strip())
        state = execute_plan(
            plan,
            registry=default_tool_registry(),
            max_steps=args.max_steps,
        )
        print(render_execution(state))
        print(summarize_execution(state))
        return

    states = run_demo_executor()
    print(f"执行 {len(states)} 份计划")
    for s in states:
        sm = summarize_execution(s)
        print(
            f"- {sm['goal']}: stop={sm['stop_reason']} "
            f"run={sm['steps_run']}/{sm['total_steps']} "
            f"status={sm['by_status']}"
        )
    print()
    if states:
        print(render_execution(states[0]))


if __name__ == "__main__":
    main()
