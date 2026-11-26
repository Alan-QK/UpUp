"""Day 61 手工试跑入口。"""

from __future__ import annotations

import argparse

from memory_window import (
    SessionMemory,
    apply_enhanced_window,
    build_demo_transcript,
    render_window_report,
)


def cmd_demo() -> None:
    msgs = build_demo_transcript()
    print("=== 原始消息 ===")
    for m in msgs:
        pin = " 📌" if m.pinned else ""
        print(f"[{m.role}]{pin} {m.content}")

    result = apply_enhanced_window(msgs, max_turns=2)
    print("\n=== max_turns=2 裁剪后 ===")
    for m in result.messages:
        pin = " 📌" if m.pinned else ""
        print(f"[{m.role}]{pin} {m.content}")
    print(
        f"\nstats: kept={result.stats.kept_messages} "
        f"dropped={result.stats.dropped_messages} "
        f"tokens_kept≈{result.stats.estimated_tokens_kept}"
    )


def cmd_budget() -> None:
    msgs = build_demo_transcript()
    # 用较紧预算观察旧轮被丢、pinned 仍在
    result = apply_enhanced_window(msgs, max_turns=4, max_tokens=40)
    print("=== max_turns=4 + max_tokens=40 ===")
    for m in result.messages:
        pin = " 📌" if m.pinned else ""
        print(f"[{m.role}]{pin} {m.content}")
    print(f"\ndropped ({len(result.dropped)}):")
    for m in result.dropped:
        print(f"  - [{m.role}] {m.content}")

    print("\n=== SessionMemory 连续追加 ===")
    mem = SessionMemory(max_turns=1, system_prompt="学习助理")
    mem.add("user", "我喜欢条目列表", pinned=True)
    mem.add_exchange("解释 RAG", "检索 + 生成。")
    mem.add_exchange("解释 Tool", "模型调外部函数。")
    for m in mem.history():
        pin = " 📌" if m.pinned else ""
        print(f"[{m.role}]{pin} {m.content}")


def cmd_report() -> None:
    result = apply_enhanced_window(build_demo_transcript(), max_turns=2, max_tokens=80)
    print(render_window_report(result))


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 61 增强历史窗口 Demo")
    parser.add_argument("--demo", action="store_true", help="按轮数裁剪演示")
    parser.add_argument("--budget", action="store_true", help="token 预算 + SessionMemory")
    parser.add_argument("--report", action="store_true", help="打印 Markdown 报告")
    args = parser.parse_args()

    if args.report:
        cmd_report()
    elif args.budget:
        cmd_budget()
    else:
        cmd_demo()


if __name__ == "__main__":
    main()
