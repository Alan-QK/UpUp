"""Day 39 tests：RAG 简易评测（纯本地）。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rag_eval import (
    CaseResult,
    EvalCase,
    EvalError,
    EvalReport,
    build_report,
    check_hit,
    evaluate_case,
    format_report_markdown,
    load_golden_set,
    parse_case,
    run_eval,
    should_refuse,
    validate_case,
)
from rag_pipeline import RetrievedChunk, index_kb_dir
from vector_store import MiniChromaClient

FIX_KB = Path(__file__).resolve().parent.parent / "fixtures" / "kb"
FIX_GOLDEN = (
    Path(__file__).resolve().parent.parent / "fixtures" / "golden" / "cases.json"
)


def _chunk(rank: int, score: float, source: str = "a.md") -> RetrievedChunk:
    return RetrievedChunk(rank, score, source, f"text-{rank}", f"{source}#{rank-1}")


def test_validate_and_parse_case() -> None:
    ok = EvalCase("c1", "什么是 RAG", False, ("rag_basics.md",))
    validate_case(ok)

    with pytest.raises(EvalError, match="id"):
        validate_case(EvalCase("  ", "q", False, ("a.md",)))
    with pytest.raises(EvalError, match="question"):
        validate_case(EvalCase("c1", "  ", False, ("a.md",)))
    with pytest.raises(EvalError, match="expect_refuse"):
        validate_case(EvalCase("c1", "q", 1, ("a.md",)))  # type: ignore[arg-type]
    with pytest.raises(EvalError, match="expected_sources"):
        validate_case(EvalCase("c1", "q", False, ()))
    with pytest.raises(EvalError, match="expected_sources"):
        validate_case(EvalCase("c1", "q", True, ("a.md",)))

    parsed = parse_case(
        {
            "id": "x",
            "question": "hello",
            "expect_refuse": True,
            "expected_sources": [],
        }
    )
    assert parsed.expect_refuse is True
    assert parsed.expected_sources == ()

    with pytest.raises(EvalError, match="object"):
        parse_case([])
    with pytest.raises(EvalError, match="missing"):
        parse_case({"id": "x"})


def test_load_golden_set(tmp_path: Path) -> None:
    cases = load_golden_set(FIX_GOLDEN)
    assert len(cases) >= 5
    assert any(c.expect_refuse for c in cases)
    assert any(not c.expect_refuse for c in cases)

    with pytest.raises(EvalError, match="file"):
        load_golden_set(tmp_path / "missing.json")

    bad = tmp_path / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    with pytest.raises(EvalError, match="list"):
        load_golden_set(bad)

    empty = tmp_path / "empty.json"
    empty.write_text("[]", encoding="utf-8")
    with pytest.raises(EvalError, match="empty"):
        load_golden_set(empty)

    dup = tmp_path / "dup.json"
    row = {
        "id": "same",
        "question": "q",
        "expect_refuse": True,
        "expected_sources": [],
    }
    dup.write_text(json.dumps([row, row]), encoding="utf-8")
    with pytest.raises(EvalError, match="duplicate"):
        load_golden_set(dup)


def test_should_refuse_and_check_hit() -> None:
    assert should_refuse([]) is True
    assert should_refuse([_chunk(1, 0.4)]) is True
    assert should_refuse([_chunk(1, 0.7)]) is False
    assert should_refuse([_chunk(1, 0.4)], min_top_score=0.3) is False

    with pytest.raises(EvalError, match="min_top_score"):
        should_refuse([_chunk(1, 0.5)], min_top_score=True)  # type: ignore[arg-type]
    with pytest.raises(EvalError, match="rank"):
        should_refuse([_chunk(2, 0.9)])

    assert check_hit([_chunk(1, 0.9, "a.md"), _chunk(2, 0.5, "b.md")], ("b.md",))
    assert not check_hit([_chunk(1, 0.9, "a.md")], ("b.md",))
    with pytest.raises(EvalError, match="expected_sources"):
        check_hit([_chunk(1, 0.9)], ())


def test_evaluate_case_answer_and_refuse() -> None:
    answer = EvalCase("a1", "q", False, ("rag_basics.md",))
    r = evaluate_case(
        answer,
        [_chunk(1, 0.8, "rag_basics.md"), _chunk(2, 0.3, "other.md")],
    )
    assert r.refused is False
    assert r.gate_ok is True
    assert r.hit is True
    assert r.top_score == pytest.approx(0.8)
    assert r.top_sources[0] == "rag_basics.md"

    miss = evaluate_case(
        answer,
        [_chunk(1, 0.8, "frontend.md")],
    )
    assert miss.hit is False
    assert miss.gate_ok is True

    low = evaluate_case(
        answer,
        [_chunk(1, 0.4, "rag_basics.md")],
    )
    assert low.refused is True
    assert low.gate_ok is False
    assert low.hit is True  # 来源对，但被阈值拒了

    refuse = EvalCase("r1", "天气", True, ())
    rr = evaluate_case(refuse, [_chunk(1, 0.2, "x.md")])
    assert rr.refused is True
    assert rr.gate_ok is True
    assert rr.hit is None

    wrong_gate = evaluate_case(refuse, [_chunk(1, 0.9, "x.md")])
    assert wrong_gate.refused is False
    assert wrong_gate.gate_ok is False
    assert wrong_gate.hit is None


def test_build_report_and_markdown() -> None:
    results = [
        CaseResult("a", "q1", False, False, True, True, 0.8, ("a.md",), "ok"),
        CaseResult("b", "q2", False, True, False, True, 0.4, ("a.md",), "low"),
        CaseResult("c", "q3", True, True, True, None, 0.2, ("x.md",), "refuse"),
    ]
    report = build_report(results)
    assert report.total == 3
    assert report.answer_cases == 2
    assert report.refuse_cases == 1
    assert report.hit_rate == pytest.approx(1.0)
    assert report.gate_accuracy == pytest.approx(2 / 3)
    assert report.pass_rate == pytest.approx(2 / 3)

    with pytest.raises(EvalError, match="empty"):
        build_report([])

    md = format_report_markdown(report)
    assert md.startswith("# RAG Eval Report")
    assert "Total: 3" in md
    assert "Hit rate: 1.0000" in md
    assert "Gate accuracy: 0.6667" in md
    assert "Pass rate: 0.6667" in md
    assert (
        "| id | expect_refuse | refused | gate_ok | hit | top_score | top1_source |"
        in md
    )
    assert "| c | true | true | true | n/a | 0.2000 | x.md |" in md
    assert "| a | false | false | true | true | 0.8000 | a.md |" in md


def test_run_eval_on_kb() -> None:
    cases = load_golden_set(FIX_GOLDEN)
    client = MiniChromaClient()
    col = client.get_or_create_collection("day39")
    assert index_kb_dir(FIX_KB, col) == 4

    report = run_eval(cases, col, k=3, min_top_score=0.55)
    assert report.total == len(cases)
    assert report.gate_accuracy == pytest.approx(1.0)
    assert report.hit_rate == pytest.approx(1.0)
    assert report.pass_rate == pytest.approx(1.0)

    with pytest.raises(EvalError, match="empty"):
        run_eval([], col)
    with pytest.raises(EvalError, match="k"):
        run_eval(cases, col, k=True)  # type: ignore[arg-type]
    with pytest.raises(EvalError, match="k"):
        run_eval(cases, col, k=0)


def test_report_type() -> None:
    cases = load_golden_set(FIX_GOLDEN)
    client = MiniChromaClient()
    col = client.get_or_create_collection("day39-type")
    index_kb_dir(FIX_KB, col)
    report = run_eval(cases[:1], col)
    assert isinstance(report, EvalReport)
    md = format_report_markdown(report)
    assert "n/a" not in md.splitlines()[0]
