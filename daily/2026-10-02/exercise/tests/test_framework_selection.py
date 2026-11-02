"""Day 51：框架选型决策器测试。"""

from __future__ import annotations

import pytest

from framework_selection import (
    ALLOWED_CANDIDATES,
    ALLOWED_GOALS,
    CANDIDATE_HANDWRITTEN,
    CANDIDATE_LANGCHAIN,
    CANDIDATE_LANGGRAPH,
    CANDIDATE_LLAMAINDEX,
    CANDIDATE_OPENAI_AGENTS_SDK,
    GOAL_LEARN_LOOP,
    GOAL_MULTI_AGENT,
    GOAL_RAG_APP,
    GOAL_SHIP_PRODUCT,
    LEVEL_ADVANCED,
    LEVEL_BEGINNER,
    LEVEL_INTERMEDIATE,
    REQUIRED_NOTE_SECTIONS,
    DecisionCase,
    ProjectContext,
    Recommendation,
    build_rejection_notes,
    default_decision_cases,
    normalize_candidate,
    normalize_goal,
    normalize_level,
    normalize_text,
    pick_primary,
    pick_secondary,
    recommend_framework,
    render_selection_note,
    validate_context,
)


def _ctx(**overrides: object) -> ProjectContext:
    base: dict[str, object] = {
        "name": "demo",
        "goal": GOAL_SHIP_PRODUCT,
        "python_level": LEVEL_ADVANCED,
        "need_multi_agent": False,
        "need_rag_first": False,
        "prefer_official_sdk": False,
        "max_frameworks": 1,
    }
    base.update(overrides)
    return ProjectContext(**base)  # type: ignore[arg-type]


def test_normalize_text() -> None:
    assert normalize_text("  少而精\n\n原则  ") == "少而精 原则"
    assert normalize_text("a\tb  c") == "a b c"
    assert normalize_text("   ") == ""


def test_normalize_goal_level_candidate() -> None:
    assert normalize_goal(" Learn_Loop ") == GOAL_LEARN_LOOP
    assert normalize_level("Beginner") == LEVEL_BEGINNER
    assert normalize_candidate(" LangGraph ") == CANDIDATE_LANGGRAPH
    with pytest.raises(ValueError, match="goal"):
        normalize_goal("finetune")
    with pytest.raises(ValueError, match="level"):
        normalize_level("expert")
    with pytest.raises(ValueError, match="candidate"):
        normalize_candidate("autogen")


def test_validate_context_rules() -> None:
    validate_context(_ctx())
    with pytest.raises(ValueError, match="name"):
        validate_context(_ctx(name="  "))
    with pytest.raises(ValueError, match="max_frameworks"):
        validate_context(_ctx(max_frameworks=3))
    with pytest.raises(ValueError, match="need_multi_agent"):
        validate_context(_ctx(goal=GOAL_MULTI_AGENT, need_multi_agent=False))
    with pytest.raises(ValueError, match="need_rag_first"):
        validate_context(_ctx(goal=GOAL_RAG_APP, need_rag_first=False))


def test_pick_primary_priority() -> None:
    assert pick_primary(_ctx(goal=GOAL_LEARN_LOOP)) == CANDIDATE_HANDWRITTEN
    assert (
        pick_primary(_ctx(goal=GOAL_SHIP_PRODUCT, python_level=LEVEL_BEGINNER))
        == CANDIDATE_HANDWRITTEN
    )
    assert (
        pick_primary(
            _ctx(
                goal=GOAL_MULTI_AGENT,
                need_multi_agent=True,
                python_level=LEVEL_ADVANCED,
            )
        )
        == CANDIDATE_LANGGRAPH
    )
    assert (
        pick_primary(
            _ctx(goal=GOAL_RAG_APP, need_rag_first=True, python_level=LEVEL_INTERMEDIATE)
        )
        == CANDIDATE_LLAMAINDEX
    )
    assert (
        pick_primary(_ctx(prefer_official_sdk=True)) == CANDIDATE_OPENAI_AGENTS_SDK
    )
    assert pick_primary(_ctx()) == CANDIDATE_LANGCHAIN


def test_pick_secondary_respects_max_and_complement() -> None:
    assert pick_secondary(_ctx(max_frameworks=1), CANDIDATE_LANGCHAIN) is None
    assert (
        pick_secondary(_ctx(max_frameworks=2), CANDIDATE_HANDWRITTEN)
        == CANDIDATE_LANGGRAPH
    )
    assert (
        pick_secondary(_ctx(max_frameworks=2), CANDIDATE_LANGGRAPH)
        == CANDIDATE_HANDWRITTEN
    )
    assert (
        pick_secondary(_ctx(max_frameworks=2), CANDIDATE_LLAMAINDEX)
        == CANDIDATE_HANDWRITTEN
    )


def test_build_rejection_notes_skips_selected() -> None:
    notes = build_rejection_notes(CANDIDATE_HANDWRITTEN, CANDIDATE_LANGGRAPH)
    names = [name for name, _ in notes]
    assert CANDIDATE_HANDWRITTEN not in names
    assert CANDIDATE_LANGGRAPH not in names
    assert set(names) == ALLOWED_CANDIDATES - {
        CANDIDATE_HANDWRITTEN,
        CANDIDATE_LANGGRAPH,
    }
    assert names == sorted(names)
    for _, why in notes:
        assert normalize_text(why)


def test_recommend_framework_bundle() -> None:
    ctx = _ctx(goal=GOAL_LEARN_LOOP, max_frameworks=2)
    rec = recommend_framework(ctx)
    assert rec.primary == CANDIDATE_HANDWRITTEN
    assert rec.secondary == CANDIDATE_LANGGRAPH
    assert len(rec.reasons) >= 2
    assert any(GOAL_LEARN_LOOP in r or "learn" in r.lower() or "手写" in r for r in rec.reasons)
    assert any(rec.primary in r or "handwritten" in r for r in rec.reasons)
    rejected_names = {name for name, _ in rec.rejected}
    assert rec.primary not in rejected_names
    assert rec.secondary not in rejected_names


def test_render_selection_note_sections() -> None:
    ctx = _ctx(goal=GOAL_LEARN_LOOP, name="转型练习", max_frameworks=2)
    rec = recommend_framework(ctx)
    note = render_selection_note(ctx, rec)
    for section in REQUIRED_NOTE_SECTIONS:
        assert f"## {section}" in note
    assert ctx.name in note
    assert rec.primary in note
    with pytest.raises(ValueError, match="reasons"):
        render_selection_note(
            ctx,
            Recommendation(
                primary=CANDIDATE_HANDWRITTEN,
                secondary=None,
                reasons=(),
                rejected=(),
            ),
        )


def test_default_decision_cases_cover_goals() -> None:
    cases = default_decision_cases()
    assert len(cases) >= 4
    goals = {normalize_goal(case.context.goal) for case in cases}
    assert goals == ALLOWED_GOALS
    for case in cases:
        assert isinstance(case, DecisionCase)
        rec = recommend_framework(case.context)
        assert rec.primary == normalize_candidate(case.expected_primary)
        assert normalize_text(case.title)
        assert normalize_text(case.teaching_point)
