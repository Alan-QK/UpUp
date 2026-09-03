"""Day 21 手工运行入口：预览结构化 Prompt。"""

from __future__ import annotations

import argparse
import json

from prompt_builder import PromptSpec, build_chat_messages


DEFAULT_USER_TEXT = (
    "我们前端同学想转 AI Agent，已经会 TypeScript，"
    "Python 还不太熟，希望有个按周推进的练习计划。"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 21 · Prompt 模板 Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="离线演示：打印 system/user messages（默认开启）",
    )
    parser.add_argument(
        "--role",
        default="你是资深技术写作教练，擅长把模糊目标拆成可执行学习任务",
        help="角色描述",
    )
    parser.add_argument(
        "--task",
        default="根据用户背景，给出未来 5 个工作日的学习重点（每天一句话）",
        help="任务描述",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        default="纯文本；共 5 行；每行形如：DayN：……",
        help="输出格式",
    )
    parser.add_argument(
        "--constraint",
        action="append",
        default=None,
        help="追加一条约束（可重复）；省略则使用默认约束集",
    )
    parser.add_argument(
        "--context",
        default="用户是高级前端，目标岗位是 AI Agent 开发工程师",
        help="可选上下文；传空字符串可去掉该章节",
    )
    parser.add_argument(
        "--user",
        "-u",
        default=DEFAULT_USER_TEXT,
        help="本轮用户输入",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 打印 messages（便于复制到 API 调试）",
    )
    return parser


def default_constraints() -> list[str]:
    return [
        "只给可执行建议，不要空话",
        "使用简体中文",
        "不要编造用户未提供的背景",
    ]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # demo 开关仅为与其他 Day 对齐；本练习默认就打印
    _ = args.demo

    constraints = (
        list(args.constraint) if args.constraint is not None else default_constraints()
    )
    context = args.context if args.context.strip() else None

    spec = PromptSpec(
        role=args.role,
        task=args.task,
        constraints=constraints,
        output_format=args.output_format,
        context=context,
    )
    messages = build_chat_messages(spec, args.user)

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
