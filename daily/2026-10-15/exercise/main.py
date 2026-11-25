"""Day 59 手工运行入口：HITL 分支 Demo / 报告。"""

from __future__ import annotations

import argparse

from hitl_confirm import (
    BRANCH_APPROVE,
    BRANCH_BLOCKED,
    BRANCH_REJECT,
    BRANCH_SAFE_AUTO,
    BRANCH_TIMEOUT,
    render_hitl_report,
    run_scenario,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 59 · HITL 确认钩子 Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="依次跑 safe_auto / approve / reject / timeout / blocked（默认）",
    )
    parser.add_argument(
        "--branch",
        choices=(
            BRANCH_SAFE_AUTO,
            BRANCH_APPROVE,
            BRANCH_REJECT,
            BRANCH_TIMEOUT,
            BRANCH_BLOCKED,
        ),
        help="只跑某一关键分支",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="输出 HITL Markdown 报告",
    )
    return parser


def print_result(branch: str) -> None:
    result = run_scenario(branch)
    print(f"=== branch={branch} ===")
    print(f"stopped_reason={result.stopped_reason}")
    print(f"llm_calls={result.llm_calls}")
    print(f"final_content={result.final_content!r}")
    print(f"refunds={result.ledger.refunds}")
    print(f"deletions={result.ledger.deletions}")
    print(f"confirmations={len(result.confirmations)}")
    for record in result.confirmations:
        print(
            f"  confirm tool={record.request.tool_name} "
            f"decision={record.decision.decision} "
            f"reason={record.request.reason!r}"
        )
    for step in result.steps:
        print(f"- step#{step.index} kind={step.kind} thought={step.thought!r}")
        for obs in step.observations:
            print(f"    obs={obs!r}")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.report:
        print(render_hitl_report())
        return 0

    if args.branch:
        print_result(args.branch)
        return 0

    for branch in (
        BRANCH_SAFE_AUTO,
        BRANCH_APPROVE,
        BRANCH_REJECT,
        BRANCH_TIMEOUT,
        BRANCH_BLOCKED,
    ):
        print_result(branch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
