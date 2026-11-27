"""Day 38 tests：拒答与低相关门控（纯本地）。"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from rag_pipeline import RetrievedChunk, index_kb_dir, retrieve
from refusal import (
    DEFAULT_REFUSAL_HINT,
    GateDecision,
    GatedAnswer,
    RefusalError,
    RefusalPolicy,
    evaluate_retrieval,
    format_refusal,
    gated_answer,
    score_margin,
    top_score,
    validate_policy,
)
from vector_store import MiniChromaClient

FIX_KB = Path(__file__).resolve().parent.parent / "fixtures" / "kb"


def _chunk(rank: int, score: float, source: str = "a.md") -> RetrievedChunk:
    return RetrievedChunk(rank, score, source, f"text-{rank}", f"{source}#{rank-1}")


def test_validate_policy() -> None:
    validate_policy(RefusalPolicy())
    with pytest.raises(RefusalError, match="min_top_score"):
        validate_policy(RefusalPolicy(min_top_score=1.5))
    with pytest.raises(RefusalError, match="min_top_score"):
        validate_policy(RefusalPolicy(min_top_score=True))  # type: ignore[arg-type]
    with pytest.raises(RefusalError, match="min_margin"):
        validate_policy(RefusalPolicy(min_margin=-0.1))
    with pytest.raises(RefusalError, match="min_margin"):
        validate_policy(RefusalPolicy(min_margin=True))  # type: ignore[arg-type]


def test_top_score_and_margin() -> None:
    assert top_score([]) is None
    assert score_margin([]) is None
    assert score_margin([_chunk(1, 0.9)]) is None

    chunks = [_chunk(1, 0.8), _chunk(2, 0.5), _chunk(3, 0.4)]
    assert top_score(chunks) == 0.8
    assert score_margin(chunks) == pytest.approx(0.3)

    with pytest.raises(RefusalError, match="rank"):
        top_score([_chunk(2, 0.5)])
    with pytest.raises(RefusalError, match="rank"):
        score_margin([_chunk(1, 0.9), _chunk(3, 0.1)])


def test_evaluate_empty_and_ok() -> None:
    empty = evaluate_retrieval([])
    assert empty.allow is False
    assert empty.reason == "empty"
    assert empty.top_score is None
    assert empty.margin is None

    ok = evaluate_retrieval(
        [_chunk(1, 0.7), _chunk(2, 0.4)],
        RefusalPolicy(min_top_score=0.55, min_margin=0.1),
    )
    assert ok.allow is True
    assert ok.reason == "ok"
    assert ok.top_score == pytest.approx(0.7)
    assert ok.margin == pytest.approx(0.3)


def test_evaluate_low_score_and_margin() -> None:
    low = evaluate_retrieval(
        [_chunk(1, 0.4), _chunk(2, 0.3)],
        RefusalPolicy(min_top_score=0.55, min_margin=0.0),
    )
    assert low.allow is False
    assert low.reason == "low_score"
    assert low.top_score == pytest.approx(0.4)

    amb = evaluate_retrieval(
        [_chunk(1, 0.8), _chunk(2, 0.78)],
        RefusalPolicy(min_top_score=0.55, min_margin=0.05),
    )
    assert amb.allow is False
    assert amb.reason == "low_margin"
    assert amb.margin == pytest.approx(0.02)

    # 单条命中：不做 margin 检查
    single = evaluate_retrieval(
        [_chunk(1, 0.9)],
        RefusalPolicy(min_top_score=0.55, min_margin=0.99),
    )
    assert single.allow is True
    assert single.reason == "ok"
    assert single.margin is None


def test_format_refusal() -> None:
    with pytest.raises(RefusalError, match="question"):
        format_refusal("  ", GateDecision(False, "empty", None, None, "x"))
    with pytest.raises(RefusalError, match="allow"):
        format_refusal("q", GateDecision(True, "ok", 0.9, 0.1, "x"))
    with pytest.raises(RefusalError, match="hint"):
        format_refusal(
            "q",
            GateDecision(False, "empty", None, None, "x"),
            hint="   ",
        )
    with pytest.raises(RefusalError, match="min_top_score"):
        format_refusal(
            "q",
            GateDecision(False, "low_score", 0.1, None, "x"),
            min_top_score=1.2,
        )

    empty = format_refusal(
        " 天气？ ",
        GateDecision(False, "empty", None, None, "no hits"),
    )
    assert empty == (
        "抱歉，我无法依据当前资料回答「天气？」。\n"
        "原因：没有检索到任何相关片段\n"
        f"建议：{DEFAULT_REFUSAL_HINT}"
    )

    low = format_refusal(
        "量子力学",
        GateDecision(False, "low_score", 0.41234, 0.1, "x"),
        hint="试试更具体的关键词",
        min_top_score=0.55,
    )
    assert low == (
        "抱歉，我无法依据当前资料回答「量子力学」。\n"
        "原因：最高相关度不足（top_score=0.4123，阈值=0.5500）\n"
        "建议：试试更具体的关键词"
    )

    low_na = format_refusal(
        "q",
        GateDecision(False, "low_score", None, None, "x"),
        min_top_score=0.6,
    )
    assert "top_score=n/a" in low_na
    assert "阈值=0.6000" in low_na

    margin = format_refusal(
        "歧义问",
        GateDecision(False, "low_margin", 0.8, 0.01234, "x"),
    )
    assert margin.split("\n")[1] == "原因：候选资料区分度不足（margin=0.0123）"

    margin_na = format_refusal(
        "q",
        GateDecision(False, "low_margin", 0.8, None, "x"),
    )
    assert margin_na.split("\n")[1] == "原因：候选资料区分度不足（margin=n/a）"

    other = format_refusal(
        "q",
        GateDecision(False, "custom", None, None, "x"),
    )
    assert other.split("\n")[1] == "原因：资料不足（custom）"


def test_gated_answer_refuses_without_calling_generate() -> None:
    called = {"n": 0}

    def boom(question: str, chunks: Sequence[RetrievedChunk]) -> str:  # noqa: ARG001
        called["n"] += 1
        raise AssertionError("should not generate when refused")

    result = gated_answer(
        " 无关问题 ",
        [_chunk(1, 0.2), _chunk(2, 0.1)],
        boom,
        policy=RefusalPolicy(min_top_score=0.55),
    )
    assert isinstance(result, GatedAnswer)
    assert result.refused is True
    assert result.reason == "low_score"
    assert called["n"] == 0
    assert "无法依据当前资料回答「无关问题」" in result.display
    assert result.answer == result.display
    assert "阈值=0.5500" in result.display


def test_gated_answer_allows_and_strips() -> None:
    def gen(question: str, chunks: Sequence[RetrievedChunk]) -> str:
        assert question == "什么是 RAG？"
        assert len(chunks) == 2
        return "  基于资料的回答[1]  "

    result = gated_answer(
        " 什么是 RAG？ ",
        [_chunk(1, 0.9), _chunk(2, 0.5)],
        gen,
        policy=RefusalPolicy(min_top_score=0.55, min_margin=0.1),
    )
    assert result.refused is False
    assert result.reason == "ok"
    assert result.answer == "基于资料的回答[1]"
    assert result.display == result.answer
    assert result.decision.allow is True


def test_gated_answer_errors() -> None:
    chunks = [_chunk(1, 0.9)]

    def gen_ok(q: str, c: Sequence[RetrievedChunk]) -> str:  # noqa: ARG001
        return "ok"

    with pytest.raises(RefusalError, match="question"):
        gated_answer("  ", chunks, gen_ok)

    def gen_bad_type(q: str, c: Sequence[RetrievedChunk]):  # noqa: ARG001
        return 123

    with pytest.raises(RefusalError, match="generate"):
        gated_answer("q", chunks, gen_bad_type)  # type: ignore[arg-type]

    def gen_blank(q: str, c: Sequence[RetrievedChunk]) -> str:  # noqa: ARG001
        return "   "

    with pytest.raises(RefusalError, match="empty"):
        gated_answer("q", chunks, gen_blank)


def test_integration_real_retrieve_refuse_and_allow() -> None:
    """端到端：相关问题放行，明显跑题问题拒答。"""
    client = MiniChromaClient()
    col = client.get_or_create_collection("day38")
    index_kb_dir(FIX_KB, col)

    policy = RefusalPolicy(min_top_score=0.55, min_margin=0.0)

    def gen(question: str, chunks: Sequence[RetrievedChunk]) -> str:
        return f"答：{question}（依据 {chunks[0].source}）"

    allow_chunks = retrieve(col, "RAG 为什么能降低幻觉", k=2)
    allowed = gated_answer("RAG 为什么能降低幻觉", allow_chunks, gen, policy=policy)
    assert allowed.refused is False
    assert allowed.decision.top_score is not None
    assert allowed.decision.top_score >= 0.55
    assert "答：" in allowed.answer

    refuse_chunks = retrieve(col, "今天天气怎么样", k=2)
    refused = gated_answer("今天天气怎么样", refuse_chunks, gen, policy=policy)
    assert refused.refused is True
    assert refused.reason == "low_score"
    assert "无法依据当前资料回答" in refused.display
