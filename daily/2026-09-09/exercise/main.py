"""Day 35 手工运行入口：本地笔记目录 → 索引 → top-k 检索（无网络）。"""

from __future__ import annotations

import argparse
from pathlib import Path

from notes_search import format_hits, index_notes_dir, search_notes
from vector_store import MiniChromaClient

DEFAULT_NOTES = Path(__file__).resolve().parent / "fixtures" / "notes"


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 35 local notes semantic search")
    parser.add_argument(
        "--notes",
        type=Path,
        default=DEFAULT_NOTES,
        help="笔记目录（默认 exercise/fixtures/notes）",
    )
    parser.add_argument(
        "--query",
        default="如何用向量检索做 RAG top-k？",
        help="查询文本",
    )
    parser.add_argument("--k", type=int, default=3, help="top-k")
    parser.add_argument("--chunk-size", type=int, default=90)
    parser.add_argument("--overlap", type=int, default=15)
    args = parser.parse_args()

    client = MiniChromaClient()
    col = client.get_or_create_collection("local-notes")
    report = index_notes_dir(
        args.notes,
        col,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )
    hits = search_notes(col, args.query, k=args.k)

    print(
        f"indexed: files={report.files}  chunks={report.chunks}  "
        f"skipped_empty={report.skipped_empty}  dims={col.dims}"
    )
    print(format_hits(hits, query=args.query))
    print("ok — Week 7 闭环：加载 → 切分 → 向量 → top-k 检索。")


if __name__ == "__main__":
    main()
