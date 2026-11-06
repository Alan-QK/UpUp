"""Day 68 入口：Reflection 反思纠错演示。"""

from __future__ import annotations

import argparse

from reflection import (
    build_sample_failed_run,
    build_sample_good_run,
    build_sample_weak_run,
    render_reflection,
    render_reflection_report,
    run_demo_reflection,
    run_reflection,
    summarize_reflection,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 68 · Reflection 反思纠错")
    parser.add_argument("--demo", action="store_true", help="批量演示反思")
    parser.add_argument("--report", action="store_true", help="输出学习报告")
    parser.add_argument(
        "--case",
        type=str,
        choices=("good", "weak", "failed"),
        default="",
        help="单情景反思",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=3,
        help="最大反思轮次",
    )
    args = parser.parse_args()

    if args.report:
        print(render_reflection_report())
        return

    cases = {
        "good": build_sample_good_run,
        "weak": build_sample_weak_run,
        "failed": build_sample_failed_run,
    }

    if args.case:
        run = cases[args.case]()
        result = run_reflection(run, max_rounds=args.max_rounds)
        print(render_reflection(result))
        print(summarize_reflection(result))
        return

    results = run_demo_reflection(max_rounds=args.max_rounds)
    print(f"反思 {len(results)} 份轨迹")
    for r in results:
        sm = summarize_reflection(r)
        print(
            f"- {sm['goal']}: decision={sm['final_decision']} "
            f"rounds={sm['rounds']} retries={sm['retries_used']}"
        )
    print()
    if results:
        print(render_reflection(results[0]))


if __name__ == "__main__":
    main()
