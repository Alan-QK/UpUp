"""Day 70 入口：多步研究任务演示。"""

from __future__ import annotations

import argparse

from research_pipeline import (
    build_demo_runs,
    render_execution,
    render_plan,
    render_research_report,
    run_research_task,
    summarize_run,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 70 · 多步研究任务")
    parser.add_argument("--demo", action="store_true", help="批量演示（happy + retry）")
    parser.add_argument("--report", action="store_true", help="输出学习报告")
    parser.add_argument("--retry-demo", action="store_true", help="注入 S2 失败后重试")
    parser.add_argument(
        "--goal",
        type=str,
        default="",
        help="自定义调研目标",
    )
    args = parser.parse_args()

    if args.report:
        print(render_research_report())
        return

    if args.retry_demo:
        run = run_research_task(
            "对比开源向量库与托管方案",
            inject_fail_step="S2",
            max_rounds=2,
        )
        print(render_plan(run.plan))
        print(render_execution(run.trace))
        print(summarize_run(run))
        return

    if args.goal.strip():
        run = run_research_task(args.goal)
        print(render_plan(run.plan))
        print(render_execution(run.trace))
        print(summarize_run(run))
        return

    runs = build_demo_runs()
    print(f"演示 {len(runs)} 次研究任务")
    for run in runs:
        sm = summarize_run(run)
        path = " → ".join(sm["state_path"])  # type: ignore[arg-type]
        print(
            f"- {sm['decision']}: rounds={sm['rounds']} steps={sm['steps']} | {path}"
        )
    print()
    if runs:
        print(render_plan(runs[0].plan))
        print(render_execution(runs[0].trace))


if __name__ == "__main__":
    main()
