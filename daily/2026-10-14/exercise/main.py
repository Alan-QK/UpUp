"""Day 58 手工运行入口：分支 Demo / 覆盖报告。"""

from __future__ import annotations

import argparse

from mock_llm_agent import (
    BRANCH_BAD_ARGS,
    BRANCH_DENY,
    BRANCH_FINAL,
    BRANCH_MAX_STEPS,
    BRANCH_TOOL_OK,
    render_coverage_report,
    run_scenario,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 58 · Mock LLM 单测 Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="依次跑 final / tool_ok / deny / bad_args / max_steps（默认）",
    )
    parser.add_argument(
        "--branch",
        choices=(
            BRANCH_FINAL,
            BRANCH_TOOL_OK,
            BRANCH_DENY,
            BRANCH_BAD_ARGS,
            BRANCH_MAX_STEPS,
        ),
        help="只跑某一关键分支",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="输出 Mock 单测覆盖 Markdown 报告",
    )
    return parser


def print_result(branch: str) -> None:
    result = run_scenario(branch)
    print(f"=== branch={branch} ===")
    print(f"stopped_reason={result.stopped_reason}")
    print(f"llm_calls={result.llm_calls}")
    print(f"final_content={result.final_content!r}")
    for step in result.steps:
        print(f"- step#{step.index} kind={step.kind} thought={step.thought!r}")
        for obs in step.observations:
            print(f"    obs={obs!r}")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.report:
        print(render_coverage_report())
        return 0

    if args.branch:
        print_result(args.branch)
        return 0

    for branch in (
        BRANCH_FINAL,
        BRANCH_TOOL_OK,
        BRANCH_DENY,
        BRANCH_BAD_ARGS,
        BRANCH_MAX_STEPS,
    ):
        print_result(branch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
