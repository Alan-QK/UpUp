"""Day 26 手工运行入口：描述 → Prompt →（mock）结构化任务 JSON。"""

from __future__ import annotations

import argparse
import json

from structured import (
    TaskBatch,
    build_structured_messages,
    parse_and_render,
    parse_task_batch,
    schema_for_prompt,
    validation_error_summary,
)
from pydantic import ValidationError


DEMO_USER = (
    "本周要把登录页改成邮箱登录，优先做；"
    "另外抽空整理一下组件文档，低优先级；"
    "还有性能排查大概要 2 小时，中等优先级，打上 perf 标签。"
)

MOCK_OK = json.dumps(
    {
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
            {
                "id": "T-3",
                "title": "性能排查",
                "priority": "medium",
                "tags": ["perf"],
                "estimate_hours": 2,
            },
        ]
    },
    ensure_ascii=False,
    indent=2,
)

# 故意非法：priority 错误 + estimate 为负，用于演示校验失败
MOCK_BAD = """好的，任务如下：
```json
{
  "tasks": [
    {
      "id": "T-1",
      "title": "登录页改为邮箱登录",
      "priority": "紧急",
      "tags": ["auth"],
      "estimate_hours": -1
    }
  ]
}
```
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 26 · 结构化输出 Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="使用内置描述 + mock 模型回复（默认推荐）",
    )
    parser.add_argument(
        "--user",
        default="",
        help="自定义用户描述（仍使用内置 mock 做解析演示）",
    )
    parser.add_argument(
        "--show-schema",
        action="store_true",
        help="打印 TaskBatch 的 JSON Schema",
    )
    parser.add_argument(
        "--show-prompt",
        action="store_true",
        help="打印组装好的 messages",
    )
    parser.add_argument(
        "--bad",
        action="store_true",
        help="使用非法 mock，演示校验失败摘要",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 打印解析后的 TaskBatch",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    user_text = args.user.strip() or DEMO_USER

    if args.show_schema:
        print("=== TaskBatch JSON Schema ===")
        print(schema_for_prompt(TaskBatch))
        print()

    messages = build_structured_messages(user_text)
    if args.show_prompt:
        print("=== messages ===")
        print(json.dumps(messages, ensure_ascii=False, indent=2))
        print()

    raw = MOCK_BAD if args.bad else MOCK_OK
    try:
        batch, md = parse_and_render(raw)
    except ValueError as exc:
        print("=== 校验/解析失败 ===")
        print(exc)
        # 若想看原始 ValidationError 结构，也可直接 model_validate
        try:
            TaskBatch.model_validate(json.loads(
                # 仅用于演示：从 bad mock 里粗暴取出 —— 正式路径请用 parse_task_batch
                raw[raw.index("{") : raw.rindex("}") + 1]
            ))
        except (ValidationError, ValueError, json.JSONDecodeError) as inner:
            if isinstance(inner, ValidationError):
                print("摘要：")
                for line in validation_error_summary(inner):
                    print(f"  - {line}")
        return 1

    if args.json:
        print(batch.model_dump_json(indent=2))
    else:
        print("=== 任务清单 ===")
        print(md)
        print()
        print(f"共 {len(batch.tasks)} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
