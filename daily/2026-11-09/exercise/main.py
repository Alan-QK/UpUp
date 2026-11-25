"""Day 69 入口：Agent 状态机演示。"""

from __future__ import annotations

import argparse

from state_machine import (
    build_demo_machines,
    render_ascii_overview,
    render_mermaid,
    render_state_machine_report,
    render_trace,
    simulate_abort_on_reflect,
    simulate_happy_path,
    simulate_hitl_approve,
    simulate_hitl_reject,
    simulate_retry_then_accept,
    simulate_revise_loop,
    summarize_machine,
)


CASES = {
    "happy": simulate_happy_path,
    "retry": simulate_retry_then_accept,
    "revise": simulate_revise_loop,
    "abort": simulate_abort_on_reflect,
    "hitl_ok": simulate_hitl_approve,
    "hitl_no": simulate_hitl_reject,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 69 · Agent 状态机")
    parser.add_argument("--demo", action="store_true", help="批量演示情景")
    parser.add_argument("--report", action="store_true", help="输出学习报告")
    parser.add_argument("--diagram", action="store_true", help="输出 Mermaid 状态图")
    parser.add_argument("--ascii", action="store_true", help="输出 ASCII 概览")
    parser.add_argument(
        "--case",
        type=str,
        choices=tuple(CASES.keys()),
        default="",
        help="单情景轨迹",
    )
    args = parser.parse_args()

    if args.report:
        print(render_state_machine_report())
        return

    if args.diagram:
        print(render_mermaid())
        return

    if args.ascii:
        print(render_ascii_overview())
        return

    if args.case:
        machine = CASES[args.case]()
        print(render_trace(machine))
        print(summarize_machine(machine))
        return

    machines = build_demo_machines()
    print(f"演示 {len(machines)} 条状态轨迹")
    for m in machines:
        sm = summarize_machine(m)
        path = " → ".join(sm["path"])  # type: ignore[arg-type]
        print(f"- {sm['final_state']}: steps={sm['steps']} | {path}")
    print()
    if machines:
        print(render_trace(machines[0]))


if __name__ == "__main__":
    main()
