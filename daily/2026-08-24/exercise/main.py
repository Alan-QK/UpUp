"""Day 23 手工运行入口：离线对比 Direct vs CoT（mock 输出）。"""

from __future__ import annotations

import argparse
import json

from cot_lab import (
    STRATEGY_COT,
    STRATEGY_DIRECT,
    ReasoningTask,
    build_messages,
    compare_outputs,
    render_report,
)


CASES: dict[str, ReasoningTask] = {
    "apples": ReasoningTask(
        case_id="apples",
        question="小明有 3 个苹果，又买了 5 个，吃掉 2 个，还剩几个？",
        expected_answer="6",
    ),
    "ages": ReasoningTask(
        case_id="ages",
        question=(
            "妈妈现在的年龄是儿子的 3 倍；6 年后妈妈年龄是儿子的 2 倍。"
            "儿子现在几岁？"
        ),
        expected_answer="6",
    ),
}

# 故意让 Direct 在 ages 上答错、CoT 答对，方便演示 cot_helped
MOCK_OUTPUTS: dict[str, dict[str, str]] = {
    "apples": {
        STRATEGY_DIRECT: "最终答案：6",
        STRATEGY_COT: (
            "1. 原有 3 个\n"
            "2. 买入后 3+5=8\n"
            "3. 吃掉 2 个后 8-2=6\n"
            "最终答案：6"
        ),
    },
    "ages": {
        STRATEGY_DIRECT: "最终答案：12",
        STRATEGY_COT: (
            "1. 设儿子现在 x 岁，则妈妈现在 3x 岁\n"
            "2. 6 年后：儿子 x+6，妈妈 3x+6\n"
            "3. 由题意 3x+6 = 2(x+6)\n"
            "4. 3x+6 = 2x+12 → x=6\n"
            "最终答案：6"
        ),
    },
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 23 · CoT 对比 Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="离线演示（默认开启）",
    )
    parser.add_argument(
        "--case",
        choices=sorted(CASES.keys()),
        default="apples",
        help="内置样例 id",
    )
    parser.add_argument(
        "--show-prompts",
        action="store_true",
        help="同时打印两套 Prompt messages",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 打印 messages（需配合 --show-prompts）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _ = args.demo

    task = CASES[args.case]
    mocks = MOCK_OUTPUTS[args.case]
    report = compare_outputs(
        task,
        direct_output=mocks[STRATEGY_DIRECT],
        cot_output=mocks[STRATEGY_COT],
    )

    if args.show_prompts:
        for strategy in (STRATEGY_DIRECT, STRATEGY_COT):
            messages = build_messages(strategy, task.question)
            print("=" * 60)
            print(f"strategy: {strategy}")
            if args.json:
                print(json.dumps(messages, ensure_ascii=False, indent=2))
            else:
                for msg in messages:
                    print("-" * 60)
                    print(f"role: {msg['role']}")
                    print(msg["content"])
        print("=" * 60)

    print(render_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
