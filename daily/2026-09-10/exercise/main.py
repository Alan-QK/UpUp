"""Day 36 手工运行入口：知识库索引 → 检索 → Prompt 拼装 → 假生成。"""

from __future__ import annotations

import argparse
from pathlib import Path

from rag_pipeline import demo_generate, index_kb_dir, run_rag
from vector_store import MiniChromaClient

DEFAULT_KB = Path(__file__).resolve().parent / "fixtures" / "kb"


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 36 minimal RAG pipeline")
    parser.add_argument(
        "--kb",
        type=Path,
        default=DEFAULT_KB,
        help="知识库目录（默认 exercise/fixtures/kb）",
    )
    parser.add_argument(
        "--query",
        default="RAG 的 Retrieve Augment Generate 三步是什么？",
        help="用户问题",
    )
    parser.add_argument("--k", type=int, default=2, help="top-k")
    args = parser.parse_args()

    client = MiniChromaClient()
    col = client.get_or_create_collection("day36-kb")
    n = index_kb_dir(args.kb, col)
    result = run_rag(col, args.query, generate_fn=demo_generate, k=args.k)

    print(f"indexed: docs={n}  dims={col.dims}  contexts={len(result.contexts)}")
    print("--- contexts ---")
    for c in result.contexts:
        preview = c.text.replace("\n", " ")[:72]
        print(f"#{c.rank} score={c.score:.4f} source={c.source}  {preview}")
    print("--- answer ---")
    print(result.answer)
    print("ok — Day 36：Retrieve → Augment → Generate 最小闭环。")


if __name__ == "__main__":
    main()
