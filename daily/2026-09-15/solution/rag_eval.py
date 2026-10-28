"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from rag_pipeline import RetrievedChunk, retrieve
from vector_store import MiniCollection

DEFAULT_MIN_TOP_SCORE = 0.55


class EvalError(ValueError):
    """评测参数、样例或状态不合法。"""


@dataclass(frozen=True)
class EvalCase:
    id: str
    question: str
    expect_refuse: bool
    expected_sources: tuple[str, ...]


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    question: str
    expect_refuse: bool
    refused: bool
    gate_ok: bool
    hit: bool | None
    top_score: float | None
    top_sources: tuple[str, ...]
    detail: str


@dataclass(frozen=True)
class EvalReport:
    total: int
    answer_cases: int
    refuse_cases: int
    hit_rate: float
    gate_accuracy: float
    pass_rate: float
    results: tuple[CaseResult, ...]


def validate_case(case: EvalCase) -> None:
    if not case.id.strip():
        raise EvalError("id must be non-empty")
    if not case.question.strip():
        raise EvalError("question must be non-empty")
    if not isinstance(case.expect_refuse, bool):
        raise EvalError("expect_refuse must be bool")

    srcs = case.expected_sources
    if not isinstance(srcs, (tuple, list)):
        raise EvalError("expected_sources must be a sequence of strings")
    for s in srcs:
        if not isinstance(s, str) or not s.strip():
            raise EvalError("expected_sources entries must be non-empty strings")

    if case.expect_refuse:
        if len(srcs) != 0:
            raise EvalError("expected_sources must be empty when expect_refuse")
    else:
        if len(srcs) == 0:
            raise EvalError("expected_sources must be non-empty when answering")


def parse_case(raw: object) -> EvalCase:
    if not isinstance(raw, dict):
        raise EvalError("case must be a JSON object")
    required = ("id", "question", "expect_refuse", "expected_sources")
    for key in required:
        if key not in raw:
            raise EvalError(f"missing key: {key}")
    srcs = raw["expected_sources"]
    if not isinstance(srcs, list):
        raise EvalError("expected_sources must be a list")
    case = EvalCase(
        id=str(raw["id"]),
        question=str(raw["question"]),
        expect_refuse=raw["expect_refuse"],
        expected_sources=tuple(srcs),
    )
    validate_case(case)
    return case


def load_golden_set(path: Path | str) -> list[EvalCase]:
    p = Path(path)
    if not p.is_file():
        raise EvalError("golden set path is not a file")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise EvalError("golden set root must be a list")
    if not data:
        raise EvalError("golden set must not be empty")

    cases: list[EvalCase] = []
    seen: set[str] = set()
    for item in data:
        case = parse_case(item)
        if case.id in seen:
            raise EvalError(f"duplicate case id: {case.id}")
        seen.add(case.id)
        cases.append(case)
    return cases


def should_refuse(
    chunks: Sequence[RetrievedChunk],
    *,
    min_top_score: float = DEFAULT_MIN_TOP_SCORE,
) -> bool:
    if isinstance(min_top_score, bool) or not (0.0 <= min_top_score <= 1.0):
        raise EvalError("min_top_score must be in [0, 1]")
    if not chunks:
        return True
    top = None
    for c in chunks:
        if c.rank == 1:
            top = c
            break
    if top is None:
        raise EvalError("missing rank==1 chunk")
    return top.score < min_top_score


def check_hit(
    chunks: Sequence[RetrievedChunk],
    expected_sources: Sequence[str],
) -> bool:
    if not expected_sources:
        raise EvalError("expected_sources must be non-empty")
    hit_set = {c.source for c in chunks}
    return any(src in hit_set for src in expected_sources)


def evaluate_case(
    case: EvalCase,
    chunks: Sequence[RetrievedChunk],
    *,
    min_top_score: float = DEFAULT_MIN_TOP_SCORE,
) -> CaseResult:
    validate_case(case)
    refused = should_refuse(chunks, min_top_score=min_top_score)
    gate_ok = refused == case.expect_refuse

    ordered = sorted(chunks, key=lambda c: c.rank)
    top_sources = tuple(c.source for c in ordered)

    top_score: float | None = None
    if chunks:
        for c in chunks:
            if c.rank == 1:
                top_score = c.score
                break
        if top_score is None:
            raise EvalError("missing rank==1 chunk")

    hit: bool | None
    if case.expect_refuse:
        hit = None
    else:
        hit = check_hit(chunks, case.expected_sources)

    detail = (
        f"refused={refused} gate_ok={gate_ok} hit={hit} "
        f"top_score={top_score}"
    )
    return CaseResult(
        case_id=case.id,
        question=case.question.strip(),
        expect_refuse=case.expect_refuse,
        refused=refused,
        gate_ok=gate_ok,
        hit=hit,
        top_score=top_score,
        top_sources=top_sources,
        detail=detail,
    )


def build_report(results: Sequence[CaseResult]) -> EvalReport:
    if not results:
        raise EvalError("results must not be empty")

    total = len(results)
    answer_cases = sum(1 for r in results if not r.expect_refuse)
    refuse_cases = sum(1 for r in results if r.expect_refuse)

    if answer_cases == 0:
        hit_rate = 0.0
    else:
        hits = sum(1 for r in results if not r.expect_refuse and r.hit is True)
        hit_rate = hits / answer_cases

    gate_ok_n = sum(1 for r in results if r.gate_ok)
    gate_accuracy = gate_ok_n / total

    passed = 0
    for r in results:
        if r.expect_refuse:
            if r.gate_ok:
                passed += 1
        else:
            if r.gate_ok and r.hit is True:
                passed += 1
    pass_rate = passed / total

    return EvalReport(
        total=total,
        answer_cases=answer_cases,
        refuse_cases=refuse_cases,
        hit_rate=hit_rate,
        gate_accuracy=gate_accuracy,
        pass_rate=pass_rate,
        results=tuple(results),
    )


def format_report_markdown(report: EvalReport) -> str:
    lines = [
        "# RAG Eval Report",
        "",
        (
            f"Total: {report.total} · "
            f"Hit rate: {report.hit_rate:.4f} · "
            f"Gate accuracy: {report.gate_accuracy:.4f} · "
            f"Pass rate: {report.pass_rate:.4f}"
        ),
        "",
        "| id | expect_refuse | refused | gate_ok | hit | top_score | top1_source |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in report.results:
        hit_s = "n/a" if r.hit is None else ("true" if r.hit else "false")
        score_s = "n/a" if r.top_score is None else f"{r.top_score:.4f}"
        top1 = r.top_sources[0] if r.top_sources else "-"
        lines.append(
            f"| {r.case_id} | "
            f"{'true' if r.expect_refuse else 'false'} | "
            f"{'true' if r.refused else 'false'} | "
            f"{'true' if r.gate_ok else 'false'} | "
            f"{hit_s} | {score_s} | {top1} |"
        )
    return "\n".join(lines) + "\n"


def run_eval(
    cases: Sequence[EvalCase],
    collection: MiniCollection,
    *,
    k: int = 3,
    min_top_score: float = DEFAULT_MIN_TOP_SCORE,
) -> EvalReport:
    if not cases:
        raise EvalError("cases must not be empty")
    if isinstance(k, bool) or k < 1:
        raise EvalError("k must be a positive int")

    results: list[CaseResult] = []
    for case in cases:
        chunks = retrieve(collection, case.question, k=k)
        results.append(
            evaluate_case(case, chunks, min_top_score=min_top_score)
        )
    return build_report(results)
