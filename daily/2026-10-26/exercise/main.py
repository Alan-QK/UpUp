"""Day 60 手工运行入口：tool-agent 演示 / 场景 / 验收报告。"""

from __future__ import annotations

import argparse
from pathlib import Path

from hitl import AlwaysApprove, ConfirmationDecision, ScriptedConfirmHook
from tool_agent import ToolAgent

DEFAULT_WORKSPACE = Path(__file__).resolve().parent / "sample_workspace"
SCENARIOS = (
    "calc_time",
    "read_notes",
    "http_docs",
    "refund_approve",
    "refund_reject",
    "blocked_shell",
    "max_steps",
)


def build_agent(args: argparse.Namespace) -> ToolAgent:
    hook: AlwaysApprove | ScriptedConfirmHook
    if args.hook == "approve":
        hook = AlwaysApprove()
    else:
        hook = ScriptedConfirmHook(
            [ConfirmationDecision(decision="reject", note="cli-default-reject")]
        )
    return ToolAgent.from_workspace(
        args.workspace,
        max_steps=args.max_steps,
        confirm_hook=hook,
    )


def cmd_demo(args: argparse.Namespace) -> None:
    agent = build_agent(args)
    for name in ("calc_time", "read_notes", "blocked_shell"):
        print(f"\n### scenario: {name}")
        # 每个场景独立实例，避免 ledger / hook 污染
        one = ToolAgent.from_workspace(
            args.workspace,
            max_steps=args.max_steps,
            confirm_hook=AlwaysApprove(),
        )
        result = one.run_scenario(name)
        print(f"stopped={result.stopped_reason} llm_calls={result.llm_calls}")
        print(f"final={result.final_content}")
        for step in result.steps:
            tools = ",".join(step.tool_names) or "-"
            print(f"  step{step.index}:{step.kind} tools={tools}")


def cmd_scenario(args: argparse.Namespace) -> None:
    agent = ToolAgent.from_workspace(
        args.workspace,
        max_steps=args.max_steps,
        confirm_hook=AlwaysApprove(),
    )
    result = agent.run_scenario(args.name)
    print(f"stopped={result.stopped_reason} llm_calls={result.llm_calls}")
    print(f"refunded={sorted(result.refunded_orders)}")
    print("--- trace ---")
    print(agent.format_trace(result), end="")


def cmd_report(args: argparse.Namespace) -> None:
    agent = build_agent(args)
    print(agent.render_acceptance_report(), end="")
    checklist = agent.acceptance_checklist()
    if all(checklist.values()):
        print("ok — Day 60：验收清单全部 PASS。")
    else:
        failed = [k for k, v in checklist.items() if not v]
        print(f"check — Day 60：未通过项：{', '.join(failed)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 60 tool-agent milestone")
    parser.add_argument(
        "--workspace", type=Path, default=DEFAULT_WORKSPACE
    )
    parser.add_argument("--max-steps", type=int, default=6)
    parser.add_argument(
        "--hook",
        choices=("approve", "reject"),
        default="approve",
        help="默认确认钩子策略（场景内部可能覆盖）",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_demo = sub.add_parser("demo", help="跑 3 个代表性场景")
    p_demo.set_defaults(func=cmd_demo)

    p_sc = sub.add_parser("scenario", help="跑单个场景")
    p_sc.add_argument("name", choices=SCENARIOS)
    p_sc.set_defaults(func=cmd_scenario)

    p_report = sub.add_parser("report", help="打印验收报告")
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
