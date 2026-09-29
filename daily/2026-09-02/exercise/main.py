"""Day 30 手工运行入口：会议原文 → 结构化纪要 → Markdown/CSV。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from meeting_minutes import (
    action_items_to_csv,
    build_minutes_messages,
    extract_minutes,
    minutes_summary,
    minutes_to_json,
    minutes_to_markdown,
)

FIXTURE = Path(__file__).parent / "fixtures" / "meeting-1.txt"

MOCK_PAYLOAD: dict[str, Any] = {
    "title": "本周产品评审会",
    "meeting_date": "2026年9月2日",
    "attendees": ["Alice", "Bob", "陈晨"],
    "decisions": [
        "采用方案 B（分阶段灰度）",
        "延期上线一周",
        "本月不再新增需求入口",
    ],
    "action_items": [
        {
            "owner": "Alice",
            "task": "更新发布计划",
            "due_date": "2026/09/05",
            "priority": "high",
        },
        {
            "owner": "Bob",
            "task": "同步设计稿给研发",
            "due_date": "2026-09-08",
            "priority": "medium",
        },
        {
            "owner": "陈晨",
            "task": "跟进灰度开关配置",
            "due_date": None,
            "priority": "low",
        },
    ],
}


def mock_complete(messages: list[dict[str, str]]) -> str:
    _ = messages
    return "好的，整理如下：\n```json\n" + json.dumps(MOCK_PAYLOAD, ensure_ascii=False) + "\n```\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 30 · 会议纪要结构化 Demo")
    parser.add_argument(
        "--format",
        choices=("markdown", "csv", "json"),
        default="markdown",
        help="导出格式（默认 markdown）",
    )
    parser.add_argument(
        "--show-prompt",
        action="store_true",
        help="打印 messages 预览",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=FIXTURE,
        help="会议原文路径（默认 fixtures/meeting-1.txt）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    text = args.file.read_text(encoding="utf-8")

    if args.show_prompt:
        msgs = build_minutes_messages(text)
        print("=== system (截断) ===")
        print(msgs[0]["content"][:500] + "...")
        print("=== user ===")
        print(msgs[1]["content"])
        print()

    minutes = extract_minutes(text, mock_complete)
    summary = minutes_summary(minutes)
    print("summary:", summary)
    print()

    if args.format == "csv":
        print(action_items_to_csv(minutes.action_items), end="")
    elif args.format == "json":
        print(minutes_to_json(minutes))
    else:
        print(minutes_to_markdown(minutes), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
