"""Day 65 手工试跑入口。"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from memory_assistant import (
    render_memory_assistant_report,
    run_cross_session_demo,
)


def cmd_demo(store: Path) -> None:
    results1, results2, stats = run_cross_session_demo(store)
    print("=== 会话 1（写入）===")
    for r in results1:
        wrote = r.wrote.text if r.wrote else "—"
        print(
            f"[{r.decision.action:5}] {r.decision.reason:18} | "
            f"{r.user_text!r} → wrote={wrote}"
        )
    print("\n=== 会话 2（新实例召回）===")
    for r in results2:
        print(f"Q: {r.user_text}")
        print(f"  hits={len(r.recalled)}")
        print(f"  {r.reply}")
    print(
        f"\n统计: turns={stats.turns} write={stats.write_count} "
        f"skip={stats.skip_count} ask={stats.ask_count} store={stats.store_size}"
    )
    print(f"store: {stats.store_path}")


def cmd_report(store: Path) -> None:
    results1, results2, stats = run_cross_session_demo(store)
    print(render_memory_assistant_report(results1, results2, stats))


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 65 带记忆助理 Demo")
    parser.add_argument("--demo", action="store_true", help="打印跨运行演示")
    parser.add_argument("--report", action="store_true", help="打印 Markdown 报告")
    parser.add_argument(
        "--store",
        type=Path,
        default=None,
        help="记忆 JSON 路径（默认用临时文件）",
    )
    args = parser.parse_args()

    if args.store is not None:
        store = args.store
    else:
        store = Path(tempfile.mkdtemp()) / "memory.json"

    if args.report:
        cmd_report(store)
    else:
        cmd_demo(store)


if __name__ == "__main__":
    main()
