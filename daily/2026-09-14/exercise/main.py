"""Day 38 手工运行入口：检索门控 + 拒答 / 放行。"""

from __future__ import annotations

import argparse
from pathlib import Path

from rag_pipeline import index_kb_dir, retrieve
from refusal import RefusalPolicy, gated_answer
from vector_store import MiniChromaClient

DEFAULT_KB = Path(__file__).resolve().parent / "fixtures" / "kb"


def demo_generate(question: str, chunks) -> str:  # noqa: ANN001
    top = chunks[0]
    preview = top.text.replace("\n", " ")[:48]
    return (
        f"根据资料，关于「{question}」可以这样理解：{preview}…"
        f"[{top.rank}]"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 38 RAG refusal gate")
    parser.add_argument(
        "--kb",
        type=Path,
        default=DEFAULT_KB,
        help="知识库目录（默认 exercise/fixtures/kb）",
    )
    parser.add_argument(
        "--query",
        default="今天天气怎么样",
        help="用户问题（默认故意跑题，便于看到拒答）",
    )
    parser.add_argument("--k", type=int, default=3, help="top-k")
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.55,
        help="min_top_score 门槛",
    )
    parser.add_argument(
        "--min-margin",
        type=float,
        default=0.0,
        help="min_margin 门槛（0 表示关闭）",
    )
    args = parser.parse_args()

    client = MiniChromaClient()
    col = client.get_or_create_collection("day38-kb")
    n = index_kb_dir(args.kb, col)
    chunks = retrieve(col, args.query, k=args.k)
    policy = RefusalPolicy(
        min_top_score=args.min_score,
        min_margin=args.min_margin,
    )

    calls = {"n": 0}

    def tracked_generate(question: str, ctxs) -> str:  # noqa: ANN001
        calls["n"] += 1
        return demo_generate(question, ctxs)

    result = gated_answer(
        args.query,
        chunks,
        tracked_generate,
        policy=policy,
    )

    print(
        f"indexed={n}  hits={len(chunks)}  "
        f"refused={result.refused}  reason={result.reason}  "
        f"generate_calls={calls['n']}"
    )
    print("--- contexts ---")
    if not chunks:
        print("(none)")
    for c in chunks:
        preview = c.text.replace("\n", " ")[:56]
        print(f"#{c.rank} score={c.score:.4f} source={c.source}  {preview}")
    print("--- decision ---")
    d = result.decision
    print(
        f"allow={d.allow} reason={d.reason} "
        f"top_score={d.top_score} margin={d.margin}"
    )
    print("--- answer ---")
    print(result.display)
    if result.refused:
        print("ok — Day 38：低相关已拒答，未调用生成。")
    else:
        print("ok — Day 38：门控放行，已生成答案。")


if __name__ == "__main__":
    main()
