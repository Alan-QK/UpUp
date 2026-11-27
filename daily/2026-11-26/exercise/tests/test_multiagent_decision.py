"""Day 71 测试：多智能体适用性决策。"""

from __future__ import annotations

import pytest

from multiagent_decision import (
    NEGATIVE_WEIGHTS,
    POSITIVE_WEIGHTS,
    REC_DEFER,
    REC_KEEP_SINGLE,
    REC_USE_MULTI,
    REQUIRED_REPORT_SECTIONS,
    USE_MULTI_MIN_POSITIVES,
    USE_MULTI_MIN_SCORE,
    Decision,
    SignalHit,
    TaskProfile,
    build_demo_decisions,
    build_demo_profiles,
    collect_signals,
    compute_score,
    decide,
    normalize_title,
    render_checklist,
    render_decision_report,
    summarize_decision,
)


def test_normalize_title() -> None:
    assert normalize_title("  调研   报告  ") == "调研 报告"
    with pytest.raises(TypeError):
        normalize_title(123)  # type: ignore[arg-type]


def test_collect_signals_and_score_stable() -> None:
    profile = TaskProfile(
        title="demo",
        distinct_roles=True,
        handoff_chain=True,
        cost_sensitive=True,
        tight_latency=True,
    )
    pros, cons = collect_signals(profile)
    assert [s.key for s in pros] == sorted(s.key for s in pros)
    assert [s.key for s in cons] == sorted(s.key for s in cons)
    assert {s.key for s in pros} == {"distinct_roles", "handoff_chain"}
    assert {s.key for s in cons} == {"cost_sensitive", "tight_latency"}
    expected = (
        POSITIVE_WEIGHTS["distinct_roles"]
        + POSITIVE_WEIGHTS["handoff_chain"]
        - NEGATIVE_WEIGHTS["cost_sensitive"]
        - NEGATIVE_WEIGHTS["tight_latency"]
    )
    assert compute_score(pros, cons) == expected


def test_blurry_roles_veto() -> None:
    d = decide(
        TaskProfile(
            title="角色说不清却想拆很多",
            blurry_roles=True,
            parallel_workstreams=True,
        )
    )
    assert d.recommendation == REC_KEEP_SINGLE
    assert "角色" in d.rationale


def test_single_skill_loop_veto() -> None:
    d = decide(
        TaskProfile(
            title="查个天气",
            single_skill_loop=True,
            tight_latency=True,
        )
    )
    assert d.recommendation == REC_KEEP_SINGLE


def test_use_multi_when_strong_signals() -> None:
    d = decide(
        TaskProfile(
            title="研究写作审校流水线",
            distinct_roles=True,
            handoff_chain=True,
            adversarial_review=True,
        )
    )
    assert d.recommendation == REC_USE_MULTI
    assert len(d.pros) >= USE_MULTI_MIN_POSITIVES
    assert d.score >= USE_MULTI_MIN_SCORE


def test_defer_when_signals_conflict_mildly() -> None:
    d = decide(
        TaskProfile(
            title="可并行但成本敏感",
            parallel_workstreams=True,
            specialty_toolsets=True,
            cost_sensitive=True,
        )
    )
    assert d.recommendation == REC_DEFER
    assert d.score > 0
    assert d.score < USE_MULTI_MIN_SCORE


def test_keep_single_when_score_non_positive() -> None:
    d = decide(
        TaskProfile(
            title="延迟与成本双杀",
            parallel_workstreams=True,
            tight_latency=True,
            cost_sensitive=True,
        )
    )
    # +1 -2 -1 = -2
    assert d.score <= 0
    assert d.recommendation == REC_KEEP_SINGLE


def test_render_checklist_and_summarize() -> None:
    d = decide(
        TaskProfile(
            title="代码生成 + 安全审计",
            distinct_roles=True,
            adversarial_review=True,
            specialty_toolsets=True,
        )
    )
    text = render_checklist(d)
    assert d.title in text
    assert "## 适用信号（Pro）" in text
    assert "## 不适用信号（Con）" in text
    assert "## 结论" in text
    assert d.recommendation in text

    sm = summarize_decision(d)
    assert sm["recommendation"] == REC_USE_MULTI
    assert sm["pro_count"] == len(d.pros)
    assert sm["con_count"] == len(d.cons)
    assert isinstance(sm["pro_keys"], list)


def test_demo_profiles_cover_three_recommendations() -> None:
    profiles = build_demo_profiles()
    assert len(profiles) == 6
    decisions = build_demo_decisions()
    assert len(decisions) == 6

    assert decisions[0].recommendation == REC_KEEP_SINGLE
    assert decisions[1].recommendation == REC_USE_MULTI
    assert decisions[2].recommendation == REC_KEEP_SINGLE
    assert decisions[3].recommendation == REC_USE_MULTI
    assert decisions[4].recommendation == REC_KEEP_SINGLE
    assert decisions[5].recommendation == REC_DEFER

    kinds = {d.recommendation for d in decisions}
    assert kinds == {REC_USE_MULTI, REC_KEEP_SINGLE, REC_DEFER}


def test_report_sections() -> None:
    report = render_decision_report()
    for section in REQUIRED_REPORT_SECTIONS:
        assert f"## {section}" in report
    assert "use_multi" in report
    assert "keep_single" in report
    assert "defer" in report


def test_decision_validation() -> None:
    with pytest.raises(ValueError):
        Decision(
            title="x",
            recommendation="noop",
            score=0,
            rationale="bad",
            pros=(),
            cons=(),
        )
    with pytest.raises(ValueError):
        SignalHit(key="", polarity="pro", weight=1, label="x")
