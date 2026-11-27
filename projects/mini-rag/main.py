"""mini-rag CLI：问答 / 评测 / 演示。"""

from __future__ import annotations

import argparse
from pathlib import Path

from mini_rag import MiniRag
from refusal import RefusalPolicy

DEFAULT_KB = Path(__file__).resolve().parent / "fixtures" / "kb"
DEFAULT_GOLDEN = (
    Path(__file__).resolve().parent / "fixtures" / "golden" / "cases.json"
)


def build_rag(args: argparse.Namespace) -> MiniRag:
    return MiniRag.from_kb_dir(
        args.kb,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        k=args.k,
        policy=RefusalPolicy(min_top_score=args.min_score),
        citation_mode=args.citation_mode,
    )


def cmd_ask(args: argparse.Namespace) -> None:
    rag = build_rag(args)
    stats = rag.index_stats
    if stats is not None:
        print(f"indexed docs={stats.documents} chunks={stats.chunks}")
    result = rag.ask(args.question)
    print(f"refused={result.refused} reason={result.reason}")
    if result.decision.top_score is not None:
        print(f"top_score={result.decision.top_score:.4f}")
    print("---")
    print(result.display)


def cmd_eval(args: argparse.Namespace) -> None:
    rag = build_rag(args)
    report = rag.evaluate(args.golden)
    print(
        f"hit_rate={report.hit_rate:.4f}  "
        f"gate_accuracy={report.gate_accuracy:.4f}  "
        f"pass_rate={report.pass_rate:.4f}"
    )
    print("--- report ---")
    print(rag.evaluate_markdown(args.golden), end="")
    if report.pass_rate >= 1.0:
        print("ok — mini-rag：golden set 全部通过。")
    else:
        print("check — mini-rag：存在未通过样例，请看报告。")


def cmd_demo(args: argparse.Namespace) -> None:
    rag = build_rag(args)
    questions = [
        "RAG 为什么能降低幻觉",
        "前端如何用 SSE 流式展示",
        "今天天气怎么样",
    ]
    for q in questions:
        print(f"\n### Q: {q}")
        result = rag.ask(q)
        flag = "REFUSE" if result.refused else "ANSWER"
        print(f"[{flag}] {result.display}")


def main() -> None:
    parser = argparse.ArgumentParser(description="mini-rag milestone")
    parser.add_argument("--kb", type=Path, default=DEFAULT_KB)
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=0.55)
    parser.add_argument("--chunk-size", type=int, default=400)
    parser.add_argument("--overlap", type=int, default=40)
    parser.add_argument(
        "--citation-mode",
        choices=("all", "mentioned"),
        default="all",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ask = sub.add_parser("ask", help="对知识库提问")
    p_ask.add_argument("question", type=str)
    p_ask.set_defaults(func=cmd_ask)

    p_eval = sub.add_parser("eval", help="跑 golden set 评测")
    p_eval.set_defaults(func=cmd_eval)

    p_demo = sub.add_parser("demo", help="跑 3 条演示问答")
    p_demo.set_defaults(func=cmd_demo)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
