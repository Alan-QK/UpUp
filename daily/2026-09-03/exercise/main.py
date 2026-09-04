"""Day 31 手工运行入口：加载 fixtures 语料并打印摘要。"""

from __future__ import annotations

import argparse
from pathlib import Path

from doc_loader import corpus_stats, load_corpus, load_document

FIXTURES = Path(__file__).parent / "fixtures"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 31 · 文档加载与清洗 Demo")
    parser.add_argument(
        "--root",
        type=Path,
        default=FIXTURES,
        help="语料根目录（默认 fixtures/）",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="只打印 corpus_stats",
    )
    parser.add_argument(
        "--show",
        type=str,
        default=None,
        help="打印指定相对路径文档的清洗结果（如 note.md）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root: Path = args.root

    docs = load_corpus(root)
    stats = corpus_stats(docs)

    if args.stats:
        print(stats)
        return 0

    if args.show:
        target = root / args.show
        doc = load_document(target, root=root)
        print(f"=== {doc.source} ({doc.suffix}) ===")
        print(f"raw={doc.raw_char_count} cleaned={doc.char_count}")
        print(doc.text, end="" if doc.text.endswith("\n") or not doc.text else "\n")
        return 0

    print(f"loaded {stats['total_docs']} docs from {root}")
    print(
        f"chars: raw={stats['total_raw_chars']} → cleaned={stats['total_chars']}"
    )
    print(f"by_suffix: {stats['by_suffix']}")
    print("sources:")
    for src in stats["sources"]:
        print(f"  - {src}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
