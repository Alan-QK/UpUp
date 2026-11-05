"""Day 57 手工运行入口：白名单演示 / 受护调用 / 输出报告。"""

from __future__ import annotations

import argparse
import json

from tool_guard import (
    authorize_tool_call,
    build_default_allowlist,
    guarded_invoke,
    render_guard_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 57 · 工具白名单与参数校验 Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="打印若干允许/拒绝样例（默认）",
    )
    parser.add_argument(
        "--call",
        metavar="TOOL",
        help="尝试受护调用指定工具名",
    )
    parser.add_argument(
        "--args",
        default="{}",
        help='工具参数 JSON 对象，默认 "{}"',
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="输出完整 Markdown 防护报告",
    )
    return parser


def print_demo() -> None:
    samples: list[tuple[str, dict]] = [
        ("order_lookup", {"order_id": "ORD-1001"}),
        ("get_time", {"unit": "ms"}),
        ("order_lookup", {}),
        ("shell_exec", {"cmd": "rm -rf /"}),
        ("Order_Lookup", {"order_id": "ORD-1002"}),
    ]
    allowlist = build_default_allowlist()
    print(f"默认允许列表：{sorted(allowlist.keys())}")
    print()
    for name, args in samples:
        decision = authorize_tool_call(name, args, allowlist)
        print(f"=== {name} {args} ===")
        print(f"decision={decision.decision}")
        print(f"reason={decision.reason}")
        if decision.decision == "allow":
            try:
                result = guarded_invoke(name, args, allowlist)
                print(f"result={result!r}")
            except Exception as exc:  # noqa: BLE001 — demo 展示
                print(f"invoke_error={exc}")
        print()


def print_call(tool: str, args_json: str) -> None:
    try:
        args = json.loads(args_json)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--args 必须是合法 JSON 对象：{exc}") from exc
    if not isinstance(args, dict):
        raise SystemExit("--args 必须是 JSON 对象")

    decision = authorize_tool_call(tool, args)
    print(f"decision={decision.decision}")
    print(f"reason={decision.reason}")
    if decision.decision != "allow":
        return
    result = guarded_invoke(tool, args)
    print(f"result={result!r}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.report:
        print(render_guard_report())
        return 0

    if args.call:
        print_call(args.call, args.args)
        return 0

    # --demo 或无参数
    print_demo()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
