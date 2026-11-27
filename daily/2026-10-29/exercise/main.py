"""Day 63 手工试跑入口。"""

from __future__ import annotations

import argparse

from vector_memory import (
    seed_demo_store,
    render_vector_memory_report,
)


def cmd_demo() -> None:
    store = seed_demo_store()
    print("=== 已写入演示偏好 ===")
    for uid in ("u-front", "u-back"):
        print(f"\n[{uid}] count={store.size(uid)}")
        for item in store.list_user(uid):
            print(f"  - {item.id}: {item.text}")

    query = "我想要深色 UI，少点动画"
    result = store.search(query, user_id="u-front", top_k=2, min_score=0.05)
    print(f"\n=== 检索：{query!r} @ u-front ===")
    for h in result.hits:
        print(f"  {h.score:.3f} · {h.item.text}")
    print("\n注入块：")
    print(result.context_block or "（无）")


def cmd_cross() -> None:
    """演示用户隔离：同一 query，不同 user 命中不同记忆。"""
    store = seed_demo_store()
    query = "写代码用什么语言？"
    print(f"=== 同一问题跨用户：{query!r} ===\n")
    for uid in ("u-front", "u-back"):
        result = store.search(query, user_id=uid, top_k=2, min_score=0.05)
        print(f"[{uid}] top_score={result.stats.top_score:.3f}")
        for h in result.hits:
            print(f"  - {h.item.text}")
        print()


def cmd_report() -> None:
    store = seed_demo_store()
    result = store.search(
        "深色主题与 TypeScript",
        user_id="u-front",
        top_k=3,
        min_score=0.05,
    )
    print(render_vector_memory_report(result))


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 63 长期向量记忆 Demo")
    parser.add_argument("--demo", action="store_true", help="写入偏好并检索")
    parser.add_argument("--cross", action="store_true", help="跨用户隔离演示")
    parser.add_argument("--report", action="store_true", help="打印 Markdown 报告")
    args = parser.parse_args()

    if args.report:
        cmd_report()
    elif args.cross:
        cmd_cross()
    else:
        cmd_demo()


if __name__ == "__main__":
    main()
