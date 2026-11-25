"""Day 27 手工运行入口：mock LLM + repair loop 演示。"""

from __future__ import annotations

import argparse
import json

from repair_loop import (
    TaskBatch,
    build_repair_user_message,
    parse_task_batch,
    run_repair_loop,
)


DEMO_MESSAGES = [
    {
        "role": "system",
        "content": (
            "你是严谨的项目助理。只输出符合 TaskBatch schema 的 JSON 对象，"
            "不要解释、不要 Markdown。"
        ),
    },
    {
        "role": "user",
        "content": "本周优先把登录页改成邮箱登录；另外低优整理组件文档。",
    },
]

OK_PAYLOAD = {
    "tasks": [
        {
            "id": "T-1",
            "title": "登录页改为邮箱登录",
            "priority": "high",
            "tags": ["auth"],
            "estimate_hours": None,
        },
        {
            "id": "T-2",
            "title": "整理组件文档",
            "priority": "low",
            "tags": ["docs"],
            "estimate_hours": None,
        },
    ]
}

BAD_PAYLOAD = {
    "tasks": [
        {
            "id": "T-1",
            "title": "登录页改为邮箱登录",
            "priority": "紧急",
            "tags": ["auth"],
            "estimate_hours": -1,
        }
    ]
}


def _ok() -> str:
    return json.dumps(OK_PAYLOAD, ensure_ascii=False, indent=2)


def _bad() -> str:
    return (
        "好的，任务如下：\n```json\n"
        + json.dumps(BAD_PAYLOAD, ensure_ascii=False, indent=2)
        + "\n```\n"
    )


class ScriptedLLM:
    """按队列返回预设回复。"""

    def __init__(self, replies: list[str]) -> None:
        self._replies = list(replies)
        self.call_count = 0

    def __call__(self, messages: list[dict[str, str]]) -> str:
        self.call_count += 1
        if not self._replies:
            raise RuntimeError("no more scripted replies")
        return self._replies.pop(0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 27 · Repair Loop Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="运行内置 mock 演示（推荐）",
    )
    parser.add_argument(
        "--fail-twice",
        action="store_true",
        help="前两次校验失败，第三次成功",
    )
    parser.add_argument(
        "--always-bad",
        action="store_true",
        help="始终返回非法 JSON，演示 exhausted",
    )
    parser.add_argument(
        "--max-repairs",
        type=int,
        default=3,
        help="最大修复次数（默认 3）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 打印 RepairResult 摘要",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.demo and not args.fail_twice and not args.always_bad:
        # 无参数时默认 demo
        args.demo = True

    if args.always_bad:
        replies = [_bad()] * (1 + max(args.max_repairs, 0))
    elif args.fail_twice:
        replies = [_bad(), "没有大括号哦", _ok()]
    else:
        replies = [_bad(), _ok()]

    llm = ScriptedLLM(replies)
    result = run_repair_loop(
        llm=llm,
        initial_messages=DEMO_MESSAGES,
        max_repairs=args.max_repairs,
    )

    if args.json:
        payload = {
            "ok": result.batch is not None,
            "repaired": result.repaired,
            "exhausted": result.exhausted,
            "llm_calls": llm.call_count,
            "attempts": [
                {
                    "attempt": a.attempt,
                    "ok": a.ok,
                    "failure_kind": a.failure_kind,
                    "error": a.error,
                }
                for a in result.attempts
            ],
            "tasks": (
                result.batch.model_dump() if isinstance(result.batch, TaskBatch) else None
            ),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if result.batch is not None else 1

    print("=== Repair Loop 结果 ===")
    print(f"llm 调用次数: {llm.call_count}")
    print(f"repaired: {result.repaired}")
    print(f"exhausted: {result.exhausted}")
    print()
    for a in result.attempts:
        status = "OK" if a.ok else f"FAIL({a.failure_kind})"
        print(f"  attempt {a.attempt}: {status}")
        if a.error:
            print(f"    error: {a.error[:120]}")
    print()

    if result.batch is None:
        print("未得到合法 TaskBatch（已用尽重试）。")
        # 顺便展示一条 repair 文案长什么样
        sample = build_repair_user_message(
            result.attempts[-1].error or "unknown",
            failure_kind=result.attempts[-1].failure_kind or "other",
            repair_index=1,
            max_repairs=max(args.max_repairs, 1),
        )
        print()
        print("=== 示例修复指令 ===")
        print(sample)
        return 1

    print("=== 任务清单 ===")
    for item in result.batch.tasks:
        print(f"- [{item.id}] {item.title} ({item.priority.value})")
    # 再验一次 parse 路径
    _ = parse_task_batch(result.attempts[-1].raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
