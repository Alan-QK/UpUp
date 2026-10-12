"""Day 37 手工运行入口：RAG 假生成 + 引用溯源展示。"""

from __future__ import annotations

import argparse
from pathlib import Path

from citations import build_cited_answer
from rag_pipeline import demo_generate, index_kb_dir, run_rag
from vector_store import MiniChromaClient

DEFAULT_KB = Path(__file__).resolve().parent / "fixtures" / "kb"


def citing_generate(messages):  # noqa: ANN001
    """演示用：在 Day36 假答案末尾挂上 [1]，方便看到溯源。"""
    return f"{demo_generate(messages)}[1]"


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 37 RAG citations")
    parser.add_argument(
        "--kb",
        type=Path,
        default=DEFAULT_KB,
        help="知识库目录（默认 exercise/fixtures/kb）",
    )
    parser.add_argument(
        "--query",
        default="RAG 为什么能降低幻觉？",
        help="用户问题",
    )
    parser.add_argument("--k", type=int, default=2, help="top-k")
    parser.add_argument(
        "--mode",
        choices=("mentioned", "all"),
        default="mentioned",
        help="引用筛选：只展示文中提到的 / 展示全部检索命中",
    )
    args = parser.parse_args()

    client = MiniChromaClient()
    col = client.get_or_create_collection("day37-kb")
    n = index_kb_dir(args.kb, col)
    rag = run_rag(col, args.query, generate_fn=citing_generate, k=args.k)
    cited = build_cited_answer(
        rag.question,
        rag.answer,
        rag.contexts,
        mode=args.mode,
    )

    print(f"indexed: docs={n}  contexts={len(rag.contexts)}  mode={args.mode}")
    print("--- contexts ---")
    for c in rag.contexts:
        preview = c.text.replace("\n", " ")[:56]
        print(f"#{c.rank} score={c.score:.4f} source={c.source}  {preview}")
    print("--- cited answer ---")
    print(cited.display)
    print("ok — Day 37：答案 + 来源 chunk 溯源。")


if __name__ == "__main__":
    main()
