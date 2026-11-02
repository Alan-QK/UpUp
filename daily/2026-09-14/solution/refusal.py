"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from rag_pipeline import RetrievedChunk

GenerateLike = Callable[[str, Sequence[RetrievedChunk]], str]

DEFAULT_REFUSAL_HINT = "请换个问法，或补充相关文档后再试。"


class RefusalError(ValueError):
    """拒答策略参数不合法。"""


@dataclass(frozen=True)
class RefusalPolicy:
    min_top_score: float = 0.55
    min_margin: float = 0.0


@dataclass(frozen=True)
class GateDecision:
    allow: bool
    reason: str
    top_score: float | None
    margin: float | None
    detail: str


@dataclass(frozen=True)
class GatedAnswer:
    question: str
    refused: bool
    reason: str
    answer: str
    display: str
    contexts: tuple[RetrievedChunk, ...]
    decision: GateDecision


def validate_policy(policy: RefusalPolicy) -> None:
    ts = policy.min_top_score
    if isinstance(ts, bool) or not (0.0 <= ts <= 1.0):
        raise RefusalError("min_top_score must be in [0, 1]")
    mg = policy.min_margin
    if isinstance(mg, bool) or mg < 0.0 or mg > 1.0:
        raise RefusalError("min_margin must be in [0, 1]")


def top_score(chunks: Sequence[RetrievedChunk]) -> float | None:
    if not chunks:
        return None
    for c in chunks:
        if c.rank == 1:
            return c.score
    raise RefusalError("missing rank==1 chunk")


def score_margin(chunks: Sequence[RetrievedChunk]) -> float | None:
    if len(chunks) < 2:
        return None
    top1 = top2 = None
    for c in chunks:
        if c.rank == 1:
            top1 = c
        elif c.rank == 2:
            top2 = c
    if top1 is None or top2 is None:
        raise RefusalError("missing rank==1 or rank==2 chunk")
    return top1.score - top2.score


def evaluate_retrieval(
    chunks: Sequence[RetrievedChunk],
    policy: RefusalPolicy | None = None,
) -> GateDecision:
    pol = policy if policy is not None else RefusalPolicy()
    validate_policy(pol)

    if not chunks:
        return GateDecision(
            allow=False,
            reason="empty",
            top_score=None,
            margin=None,
            detail="no retrieval hits",
        )

    ts = top_score(chunks)
    assert ts is not None
    margin: float | None = score_margin(chunks) if len(chunks) >= 2 else None

    if ts < pol.min_top_score:
        return GateDecision(
            allow=False,
            reason="low_score",
            top_score=ts,
            margin=margin,
            detail=f"top_score {ts:.4f} < {pol.min_top_score:.4f}",
        )

    if margin is not None and margin < pol.min_margin:
        return GateDecision(
            allow=False,
            reason="low_margin",
            top_score=ts,
            margin=margin,
            detail=f"margin {margin:.4f} < {pol.min_margin:.4f}",
        )

    return GateDecision(
        allow=True,
        reason="ok",
        top_score=ts,
        margin=margin,
        detail="retrieval passed gate",
    )


def _fmt_score(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.4f}"


def format_refusal(
    question: str,
    decision: GateDecision,
    *,
    hint: str = DEFAULT_REFUSAL_HINT,
    min_top_score: float = 0.55,
) -> str:
    q = question.strip()
    if not q:
        raise RefusalError("question must be non-empty")
    if decision.allow:
        raise RefusalError("cannot format refusal when allow is True")
    h = hint.strip()
    if not h:
        raise RefusalError("hint must be non-empty")
    if isinstance(min_top_score, bool) or not (0.0 <= min_top_score <= 1.0):
        raise RefusalError("min_top_score must be in [0, 1]")

    reason = decision.reason
    if reason == "empty":
        reason_text = "没有检索到任何相关片段"
    elif reason == "low_score":
        reason_text = (
            f"最高相关度不足（top_score={_fmt_score(decision.top_score)}，"
            f"阈值={min_top_score:.4f}）"
        )
    elif reason == "low_margin":
        reason_text = f"候选资料区分度不足（margin={_fmt_score(decision.margin)}）"
    else:
        reason_text = f"资料不足（{reason}）"

    return (
        f"抱歉，我无法依据当前资料回答「{q}」。\n"
        f"原因：{reason_text}\n"
        f"建议：{h}"
    )


def gated_answer(
    question: str,
    chunks: Sequence[RetrievedChunk],
    generate_fn: GenerateLike,
    *,
    policy: RefusalPolicy | None = None,
    hint: str = DEFAULT_REFUSAL_HINT,
) -> GatedAnswer:
    q = question.strip()
    if not q:
        raise RefusalError("question must be non-empty")

    pol = policy if policy is not None else RefusalPolicy()
    decision = evaluate_retrieval(chunks, pol)

    if not decision.allow:
        text = format_refusal(
            q,
            decision,
            hint=hint,
            min_top_score=pol.min_top_score,
        )
        return GatedAnswer(
            question=q,
            refused=True,
            reason=decision.reason,
            answer=text,
            display=text,
            contexts=tuple(chunks),
            decision=decision,
        )

    raw = generate_fn(q, chunks)
    if not isinstance(raw, str):
        raise RefusalError("generate must return str")
    answer = raw.strip()
    if not answer:
        raise RefusalError("empty generated answer")

    return GatedAnswer(
        question=q,
        refused=False,
        reason="ok",
        answer=answer,
        display=answer,
        contexts=tuple(chunks),
        decision=decision,
    )
