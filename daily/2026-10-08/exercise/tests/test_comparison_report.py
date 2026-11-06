"""Day 55：手写 vs 框架对比报告测试。"""

from __future__ import annotations

import pytest

from comparison_report import (
    ALLOWED_DIMENSIONS,
    APPROACH_FRAMEWORK,
    APPROACH_HANDWRITTEN,
    DIMENSION_CLARITY,
    DIMENSION_CONTROL,
    DIMENSION_DEBUG,
    DIMENSION_EXTENSIBILITY,
    DIMENSION_LABELS,
    DIMENSION_LOCKIN,
    DIMENSION_VELOCITY,
    GOAL_INTERVIEW,
    GOAL_LEARN_LOOP,
    GOAL_ONBOARD,
    GOAL_SHIP_PRODUCT,
    REQUIRED_REPORT_SECTIONS,
    WEEK11_RETROSPECTIVE,
    DimensionScore,
    normalize_approach,
    normalize_dimension,
    normalize_goal,
    normalize_text,
    recommend_for_goal,
    recommendation_reason,
    render_comparison_report,
    render_score_table,
    score_delta,
    summarize_side_wins,
    validate_dimension_score,
    validate_score_value,
    week11_default_scores,
)


def _score(
    dimension: str,
    handwritten: int,
    framework: int,
    note: str = "ok",
) -> DimensionScore:
    return DimensionScore(
        dimension=dimension,
        handwritten=handwritten,
        framework=framework,
        note=note,
    )


def test_normalize_text() -> None:
    assert normalize_text("  手写\n\n对比  ") == "手写 对比"
    assert normalize_text("a\tb  c") == "a b c"
    assert normalize_text("   ") == ""


def test_normalize_approach_dimension_goal() -> None:
    assert normalize_approach(" HandWritten ") == APPROACH_HANDWRITTEN
    assert normalize_approach("FRAMEWORK") == APPROACH_FRAMEWORK
    assert normalize_dimension(" Control ") == DIMENSION_CONTROL
    assert normalize_goal(" Learn_Loop ") == GOAL_LEARN_LOOP
    with pytest.raises(ValueError, match="approach"):
        normalize_approach("langchain")
    with pytest.raises(ValueError, match="dimension"):
        normalize_dimension("latency")
    with pytest.raises(ValueError, match="goal"):
        normalize_goal("finetune")


def test_validate_score_value() -> None:
    validate_score_value(1)
    validate_score_value(5)
    with pytest.raises(ValueError, match="score"):
        validate_score_value(0)
    with pytest.raises(ValueError, match="score"):
        validate_score_value(6)
    with pytest.raises(ValueError, match="score"):
        validate_score_value(True)  # type: ignore[arg-type]


def test_validate_dimension_score() -> None:
    validate_dimension_score(_score(DIMENSION_CONTROL, 5, 3, "掌控 Loop"))
    with pytest.raises(ValueError, match="dimension"):
        validate_dimension_score(_score("latency", 3, 3))
    with pytest.raises(ValueError, match="score"):
        validate_dimension_score(_score(DIMENSION_CONTROL, 0, 3))
    with pytest.raises(ValueError, match="note"):
        validate_dimension_score(_score(DIMENSION_CONTROL, 3, 3, "  "))


def test_week11_default_scores_shape_and_values() -> None:
    scores = week11_default_scores()
    assert len(scores) == 6
    by_dim = {item.dimension: item for item in scores}
    assert set(by_dim) == ALLOWED_DIMENSIONS

    expected = {
        DIMENSION_CONTROL: (5, 3),
        DIMENSION_CLARITY: (5, 3),
        DIMENSION_VELOCITY: (2, 5),
        DIMENSION_EXTENSIBILITY: (3, 4),
        DIMENSION_DEBUG: (5, 3),
        DIMENSION_LOCKIN: (5, 2),
    }
    for dimension, (hw, fw) in expected.items():
        item = by_dim[dimension]
        assert item.handwritten == hw
        assert item.framework == fw
        assert normalize_text(item.note)
        validate_dimension_score(item)


def test_score_delta_and_side_wins() -> None:
    scores = week11_default_scores()
    assert score_delta(scores[0]) == scores[0].handwritten - scores[0].framework

    wins = summarize_side_wins(scores)
    assert DIMENSION_CONTROL in wins.handwritten
    assert DIMENSION_CLARITY in wins.handwritten
    assert DIMENSION_DEBUG in wins.handwritten
    assert DIMENSION_LOCKIN in wins.handwritten
    assert DIMENSION_VELOCITY in wins.framework
    assert DIMENSION_EXTENSIBILITY in wins.framework
    assert wins.ties == ()

    with pytest.raises(ValueError, match="empty"):
        summarize_side_wins([])

    incomplete = (
        _score(DIMENSION_CONTROL, 5, 3),
        _score(DIMENSION_CLARITY, 5, 3),
    )
    with pytest.raises(ValueError, match="missing"):
        summarize_side_wins(incomplete)

    dup = week11_default_scores() + (_score(DIMENSION_CONTROL, 4, 4),)
    with pytest.raises(ValueError, match="duplicate"):
        summarize_side_wins(dup)


def test_recommend_for_goal_rules() -> None:
    assert recommend_for_goal(GOAL_LEARN_LOOP) == APPROACH_HANDWRITTEN
    assert recommend_for_goal(GOAL_INTERVIEW) == APPROACH_HANDWRITTEN
    assert recommend_for_goal(GOAL_SHIP_PRODUCT) == APPROACH_FRAMEWORK
    assert recommend_for_goal(GOAL_ONBOARD) == APPROACH_FRAMEWORK
    assert normalize_text(recommendation_reason(GOAL_LEARN_LOOP))
    assert normalize_text(recommendation_reason(GOAL_SHIP_PRODUCT))


def test_render_score_table() -> None:
    table = render_score_table(week11_default_scores())
    assert table.splitlines()[0].startswith("| 维度 |")
    assert "---" in table.splitlines()[1]
    for label in DIMENSION_LABELS.values():
        assert label in table
    assert "5" in table and "2" in table


def test_render_comparison_report_sections() -> None:
    report = render_comparison_report(GOAL_LEARN_LOOP)
    for section in REQUIRED_REPORT_SECTIONS:
        assert f"## {section}" in report

    for day, summary in WEEK11_RETROSPECTIVE:
        assert f"Day {day}" in report
        assert summary in report

    assert "`learn_loop`" in report
    assert f"`{APPROACH_HANDWRITTEN}`" in report
    assert "可控性" in report
    assert "Prompt Injection" in report or "Week 12" in report

    ship = render_comparison_report(GOAL_SHIP_PRODUCT)
    assert f"`{APPROACH_FRAMEWORK}`" in ship
    assert "`ship_product`" in ship


def test_custom_scores_in_report() -> None:
    custom = tuple(
        _score(dim, 3, 3, f"平局-{dim}")
        for dim in (
            DIMENSION_CONTROL,
            DIMENSION_CLARITY,
            DIMENSION_VELOCITY,
            DIMENSION_EXTENSIBILITY,
            DIMENSION_DEBUG,
            DIMENSION_LOCKIN,
        )
    )
    report = render_comparison_report(GOAL_INTERVIEW, scores=custom)
    assert "平局-control" in report or "平局" in report
    wins = summarize_side_wins(custom)
    assert wins.handwritten == ()
    assert wins.framework == ()
    assert set(wins.ties) == ALLOWED_DIMENSIONS
