"""Day 5 手工运行入口：笔记 CLI。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from note_store import NoteNotFoundError, NoteStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="notes", description="迷你笔记 CLI（Day 5）")
    parser.add_argument(
        "--file",
        type=Path,
        default=Path("notes.json"),
        help="笔记 JSON 文件路径（默认 notes.json）",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add", help="新增笔记")
    add_p.add_argument("title")
    add_p.add_argument("body")

    sub.add_parser("list", help="列出全部笔记")

    get_p = sub.add_parser("get", help="按 id 查看")
    get_p.add_argument("id", type=int)

    del_p = sub.add_parser("delete", help="按 id 删除")
    del_p.add_argument("id", type=int)

    search_p = sub.add_parser("search", help="搜索标题/正文")
    search_p.add_argument("query")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = NoteStore(args.file)

    try:
        if args.command == "add":
            note = store.add(args.title, args.body)
            print(f"created #{note.id}: {note.title}")
            return 0

        if args.command == "list":
            notes = store.list_notes()
            if not notes:
                print("(empty)")
                return 0
            for note in notes:
                print(f"#{note.id}\t{note.title}\t{note.created_at}")
            return 0

        if args.command == "get":
            note = store.get(args.id)
            print(f"#{note.id} {note.title}")
            print(note.body)
            return 0

        if args.command == "delete":
            store.delete(args.id)
            print(f"deleted #{args.id}")
            return 0

        if args.command == "search":
            notes = store.search(args.query)
            if not notes:
                print("(no match)")
                return 0
            for note in notes:
                print(f"#{note.id}\t{note.title}")
            return 0

    except NoteNotFoundError:
        print(f"error: note #{getattr(args, 'id', '?')} not found", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
