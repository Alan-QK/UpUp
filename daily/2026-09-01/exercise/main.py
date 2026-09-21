"""Day 29 手工运行入口：批量名片文本 → Contact → JSON/CSV。"""

from __future__ import annotations

import argparse
import json
from typing import Any

from batch_extract import (
    batch_summary,
    build_extract_messages,
    contacts_to_csv,
    contacts_to_json,
    extract_batch,
    successful_contacts,
)

SAMPLES: list[tuple[str, str]] = [
    (
        "card-1",
        "名片：王敏，示例云科技公司，产品经理。邮箱 wangmin@example.com，手机 138-1234-5678。标签：产品、B端。",
    ),
    (
        "card-2",
        "Hi, I'm Alex Chen from Northwind. Reach me at alex.chen@northwind.io or +1 (415) 555-0100. Title: Staff Engineer. Tags: backend.",
    ),
    (
        "card-3",
        "备注：下周找「赵倩」对一下设计稿，她是协作方「青禾设计」的设计师，微信同手机 15900001111，没留邮箱。",
    ),
]

MOCK_BY_ID: dict[str, dict[str, Any]] = {
    "card-1": {
        "name": "王敏",
        "email": "wangmin@example.com",
        "phone": "138-1234-5678",
        "company": "示例云科技公司",
        "title": "产品经理",
        "tags": ["产品", "B端"],
    },
    "card-2": {
        "name": "Alex Chen",
        "email": "alex.chen@northwind.io",
        "phone": "+1 (415) 555-0100",
        "company": "Northwind",
        "title": "Staff Engineer",
        "tags": ["backend"],
    },
    "card-3": {
        "name": "赵倩",
        "email": None,
        "phone": "15900001111",
        "company": "青禾设计",
        "title": "设计师",
        "tags": [],
    },
}


def mock_complete(messages: list[dict[str, str]], *, fail_one: bool) -> str:
    user = messages[1]["content"]
    for sid, text in SAMPLES:
        if text.strip() in user:
            if fail_one and sid == "card-2":
                return "抱歉，这条无法抽取。"
            payload = MOCK_BY_ID[sid]
            return "```json\n" + json.dumps(payload, ensure_ascii=False) + "\n```"
    return "{}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 29 · 批量信息抽取 Demo")
    parser.add_argument(
        "--format",
        choices=("json", "csv"),
        default="json",
        help="成功记录导出格式（默认 json）",
    )
    parser.add_argument(
        "--fail-one",
        action="store_true",
        help="让 card-2 的 mock 返回非 JSON，演示失败隔离",
    )
    parser.add_argument(
        "--show-prompt",
        action="store_true",
        help="打印第一条的 messages 预览",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.show_prompt:
        msgs = build_extract_messages(SAMPLES[0][1])
        print("=== system (截断) ===")
        print(msgs[0]["content"][:500] + "...")
        print("=== user ===")
        print(msgs[1]["content"])
        print()

    def complete_fn(messages: list[dict[str, str]]) -> str:
        return mock_complete(messages, fail_one=args.fail_one)

    results = extract_batch(SAMPLES, complete_fn)
    summary = batch_summary(results)
    print("summary:", summary)
    for r in results:
        if r.ok and r.contact:
            print(f"  ✓ {r.source_id}: {r.contact.name}")
        else:
            print(f"  ✗ {r.source_id}: {r.error}")

    contacts = successful_contacts(results)
    print()
    if args.format == "csv":
        print(contacts_to_csv(contacts), end="")
    else:
        print(contacts_to_json(contacts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
