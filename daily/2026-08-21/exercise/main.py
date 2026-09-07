"""Day 22 手工运行入口：预览 few-shot 分类 Prompt。"""

from __future__ import annotations

import argparse
import json

from few_shot import (
    KIND_COUNTER,
    KIND_POSITIVE,
    ClassificationPrompt,
    ShotExample,
    build_classification_messages,
)


DEFAULT_TEXT = "登录按钮点了没反应，一直转圈"


def default_examples() -> list[ShotExample]:
    return [
        ShotExample("支付失败一直转圈，控制台有 500", "bug", kind=KIND_POSITIVE),
        ShotExample("希望支持导出 CSV", "feature", kind=KIND_POSITIVE),
        ShotExample("怎么重置密码？", "question", kind=KIND_POSITIVE),
        ShotExample(
            "暗黑模式什么时候有？语气有点急",
            "feature",
            kind=KIND_COUNTER,
            note="这是功能请求，不是缺陷",
        ),
        ShotExample(
            "你们文档里登录流程怎么走？",
            "question",
            kind=KIND_COUNTER,
            note="纯咨询用法，即使提到登录也不要标成 bug",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 22 · Few-shot 分类 Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="离线演示：打印 system/user messages（默认开启）",
    )
    parser.add_argument(
        "--task",
        default="将用户工单分类到指定标签",
        help="任务描述",
    )
    parser.add_argument(
        "--labels",
        default="bug,feature,question",
        help="逗号分隔的标签集合",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        default="只输出一个标签：bug / feature / question，不要解释",
        help="输出格式",
    )
    parser.add_argument(
        "--text",
        "-t",
        default=DEFAULT_TEXT,
        help="待分类文本",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 打印 messages（便于复制到 API 调试）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _ = args.demo

    labels = [part.strip() for part in args.labels.split(",") if part.strip()]
    spec = ClassificationPrompt(
        task=args.task,
        labels=labels,
        examples=default_examples(),
        output_format=args.output_format,
    )
    messages = build_classification_messages(spec, args.text)

    if args.json:
        print(json.dumps(messages, ensure_ascii=False, indent=2))
        return 0

    for msg in messages:
        print("=" * 60)
        print(f"role: {msg['role']}")
        print("-" * 60)
        print(msg["content"])
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
