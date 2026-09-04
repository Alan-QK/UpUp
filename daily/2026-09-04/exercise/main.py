"""Day 32 手工运行入口：对样例文本做固定窗口切分。"""

from __future__ import annotations

import argparse
import textwrap

from chunker import Document, chunk_corpus, chunk_stats, chunk_text

SAMPLE = textwrap.dedent(
    """\
    RAG 把长文档切成小块再检索。切块太大，噪声多；切块太小，语义碎。
    固定窗口简单可复现：选定 chunk_size 与 overlap，按 step 滑动。
    overlap 让相邻块共享一段上下文，降低「关键句正好落在切缝」的风险。
    每个 chunk 应保留 source 与字符偏移，方便回答时引用原文。
    """
).strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 32 · Chunking Demo")
    parser.add_argument("--size", type=int, default=60, help="chunk_size（字符）")
    parser.add_argument("--overlap", type=int, default=12, help="overlap（字符）")
    parser.add_argument(
        "--stats",
        action="store_true",
        help="只打印 chunk_stats（对 SAMPLE + 短文档语料）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.stats:
        docs = [
            Document("sample.txt", SAMPLE),
            Document("short.txt", "短文本整块即可。"),
        ]
        chunks = chunk_corpus(docs, chunk_size=args.size, overlap=args.overlap)
        print(chunk_stats(chunks))
        return 0

    chunks = chunk_text(
        SAMPLE,
        chunk_size=args.size,
        overlap=args.overlap,
        source="sample.txt",
    )
    step = args.size - args.overlap
    print(
        f"text_len={len(SAMPLE)} chunk_size={args.size} "
        f"overlap={args.overlap} step={step} → {len(chunks)} chunks"
    )
    for c in chunks:
        preview = c.text.replace("\n", " ")
        if len(preview) > 48:
            preview = preview[:48] + "…"
        print(f"[{c.index}] [{c.start}:{c.end}) ({c.char_count}) {preview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
