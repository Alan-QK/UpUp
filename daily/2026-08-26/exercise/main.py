"""Day 25 手工运行入口：需求 → Prompt →（mock）JSON 用户故事。"""

from __future__ import annotations

import argparse
import json

from user_story import (
    StoryExample,
    generate_stories_from_response,
    render_stories_markdown,
    stories_to_dict,
)


DEMO_REQUIREMENT = (
    "我们要做一个在线课程学习小程序：学员能浏览课程列表、收藏课程、"
    "查看本周学习进度；讲师能上传课时。先做学员侧核心路径。"
)

DEMO_EXAMPLE = StoryExample(
    requirement="用户可以邮箱登录",
    stories=[
        {
            "id": "US-1",
            "title": "邮箱登录",
            "as_a": "注册用户",
            "i_want": "使用邮箱和密码登录",
            "so_that": "进入个人学习空间",
            "acceptance_criteria": [
                "正确凭证可进入首页",
                "错误凭证给出明确提示且不进入系统",
            ],
            "priority": "must",
        }
    ],
)

# 离线 mock：假装模型已经按 schema 返回
MOCK_RESPONSE = json.dumps(
    {
        "stories": [
            {
                "id": "US-1",
                "title": "浏览课程列表",
                "as_a": "学员",
                "i_want": "看到可学习的课程列表",
                "so_that": "选择感兴趣的课程开始学习",
                "acceptance_criteria": [
                    "列表展示课程标题与简介",
                    "无课程时显示空态提示",
                ],
                "priority": "must",
            },
            {
                "id": "US-2",
                "title": "收藏课程",
                "as_a": "学员",
                "i_want": "把课程加入收藏",
                "so_that": "稍后能快速找到",
                "acceptance_criteria": [
                    "点击收藏后状态变为已收藏",
                    "收藏列表可看到该课程",
                ],
                "priority": "should",
            },
            {
                "id": "US-3",
                "title": "查看本周学习进度",
                "as_a": "学员",
                "i_want": "在首页看到本周完成课时",
                "so_that": "合理安排剩余学习时间",
                "acceptance_criteria": [
                    "展示本周已完成课时数字",
                    "数字与学习记录一致",
                ],
                "priority": "must",
            },
        ]
    },
    ensure_ascii=False,
    indent=2,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 25 · 用户故事生成器 Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="使用内置需求 + mock 模型回复（默认推荐）",
    )
    parser.add_argument(
        "--requirement",
        default="",
        help="自定义需求文本（仍使用内置 mock 回复做解析演示）",
    )
    parser.add_argument(
        "--show-prompt",
        action="store_true",
        help="打印组装好的 messages",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 打印解析后的 stories",
    )
    parser.add_argument(
        "--no-few-shot",
        action="store_true",
        help="不附带 few-shot 示例",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    requirement = args.requirement.strip() or DEMO_REQUIREMENT
    examples = None if args.no_few_shot else [DEMO_EXAMPLE]

    messages, stories = generate_stories_from_response(
        requirement,
        MOCK_RESPONSE,
        examples=examples,
    )

    if args.show_prompt:
        print("=== messages ===")
        print(json.dumps(messages, ensure_ascii=False, indent=2))
        print()

    if args.json:
        print(json.dumps(stories_to_dict(stories), ensure_ascii=False, indent=2))
    else:
        print("=== 用户故事（Markdown）===")
        print(render_stories_markdown(stories))
        print()
        print(f"共 {len(stories)} 条 · 需求摘要：{requirement[:48]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
