"""Day 39 手工运行入口：加载 golden set → 检索评测 → 打印 Markdown 报告。"""

from __future__ import annotations

import argparse
from pathlib import Path

from rag_eval import format_report_markdown, load_golden_set, run_eval
from rag_pipeline import index_kb_dir
from vector_store import MiniChromaClient

DEFAULT_KB = Path(__file__).resolve().parent / "fixtures" / "kb"
DEFAULT_GOLDEN = (
    Path(__file__).resolve().parent / "fixtures" / "golden" / "cases.json"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 39 RAG golden-set eval")
    parser.add_argument("--kb", type=Path, default=DEFAULT_KB)
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=0.55)
    args = parser.parse_args()

    cases = load_golden_set(args.golden)
    client = MiniChromaClient()
    col = client.get_or_create_collection("day39-kb")
    n = index_kb_dir(args.kb, col)
    report = run_eval(
        cases,
        col,
        k=args.k,
        min_top_score=args.min_score,
    )

    print(f"indexed={n}  cases={report.total}")
    print(
        f"hit_rate={report.hit_rate:.4f}  "
        f"gate_accuracy={report.gate_accuracy:.4f}  "
        f"pass_rate={report.pass_rate:.4f}"
    )
    print("--- report ---")
    print(format_report_markdown(report), end="")
    if report.pass_rate >= 1.0:
        print("ok — Day 39：golden set 全部通过。")
    else:
        print("check — Day 39：存在未通过样例，请看报告表格。")


if __name__ == "__main__":
    main()
