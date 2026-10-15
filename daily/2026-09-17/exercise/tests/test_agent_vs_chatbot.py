"""Day 41：Chatbot vs Agent 对照与分类。"""

from __future__ import annotations

import pytest

from agent_vs_chatbot import (
    ALLOWED_KINDS,
    KIND_AGENT,
    KIND_CHATBOT,
    REQUIRED_DIMENSIONS,
    ComparisonRow,
    ScenarioExample,
    classify_by_signals,
    default_comparison_rows,
    default_scenarios,
    normalize_kind,
    normalize_text,
    render_comparison_markdown,
    render_examples_report,
    validate_comparison_row,
    validate_scenario,
)


def test_normalize_text() -> None:
    assert normalize_text("  你好\n\n世界  ") == "你好 世界"
    assert normalize_text("a\tb  c") == "a b c"
    assert normalize_text("   ") == ""


def test_normalize_kind() -> None:
    assert normalize_kind(" ChatBot ") == KIND_CHATBOT
    assert normalize_kind("AGENT") == KIND_AGENT
    with pytest.raises(ValueError, match="kind"):
        normalize_kind("assistant")


def test_classify_by_signals_rules() -> None:
    assert (
        classify_by_signals(
            needs_tools=False,
            needs_multi_step=False,
            has_side_effects=False,
        )
        == KIND_CHATBOT
    )
    # 多步推理 alone 仍是 chatbot
    assert (
        classify_by_signals(
            needs_tools=False,
            needs_multi_step=True,
            has_side_effects=False,
        )
        == KIND_CHATBOT
    )
    assert (
        classify_by_signals(
            needs_tools=True,
            needs_multi_step=False,
            has_side_effects=False,
        )
        == KIND_AGENT
    )
    assert (
        classify_by_signals(
            needs_tools=False,
            needs_multi_step=False,
            has_side_effects=True,
        )
        == KIND_AGENT
    )
    assert (
        classify_by_signals(
            needs_tools=True,
            needs_multi_step=True,
            has_side_effects=True,
        )
        == KIND_AGENT
    )


def test_validate_comparison_row() -> None:
    validate_comparison_row(
        ComparisonRow("核心能力", "生成文本", "调用工具")
    )
    with pytest.raises(ValueError, match="dimension"):
        validate_comparison_row(ComparisonRow("  ", "a", "b"))
    with pytest.raises(ValueError, match="chatbot"):
        validate_comparison_row(ComparisonRow("核心能力", "\n", "b"))
    with pytest.raises(ValueError, match="agent"):
        validate_comparison_row(ComparisonRow("核心能力", "a", "   "))


def test_validate_scenario_consistency() -> None:
    ok = ScenarioExample(
        title="查日历",
        user_goal="看看明天有没有会",
        needs_tools=True,
        needs_multi_step=False,
        has_side_effects=False,
        expected_kind=KIND_AGENT,
        rationale="需要日历工具",
    )
    validate_scenario(ok)

    bad = ScenarioExample(
        title="纯闲聊",
        user_goal="随便聊聊",
        needs_tools=False,
        needs_multi_step=False,
        has_side_effects=False,
        expected_kind=KIND_AGENT,  # 与信号矛盾
        rationale="其实不该是 agent",
    )
    with pytest.raises(ValueError, match="inconsistent"):
        validate_scenario(bad)


def test_validate_scenario_empty_fields() -> None:
    with pytest.raises(ValueError, match="title"):
        validate_scenario(
            ScenarioExample(
                title=" ",
                user_goal="目标",
                needs_tools=False,
                needs_multi_step=False,
                has_side_effects=False,
                expected_kind=KIND_CHATBOT,
                rationale="理由",
            )
        )


def test_default_comparison_rows_cover_required() -> None:
    rows = default_comparison_rows()
    assert len(rows) >= 5
    dims = {normalize_text(row.dimension) for row in rows}
    for required in REQUIRED_DIMENSIONS:
        assert required in dims
    for row in rows:
        validate_comparison_row(row)


def test_render_comparison_markdown() -> None:
    md = render_comparison_markdown(default_comparison_rows())
    lines = md.splitlines()
    assert lines[0] == "| 维度 | Chatbot | Agent |"
    assert lines[1] == "| --- | --- | --- |"
    assert len(lines) >= 7  # header + sep + ≥5 rows
    assert "核心能力" in md
    with pytest.raises(ValueError, match="empty"):
        render_comparison_markdown([])


def test_default_scenarios_balance() -> None:
    examples = default_scenarios()
    assert len(examples) >= 4
    kinds = {normalize_kind(ex.expected_kind) for ex in examples}
    assert kinds == ALLOWED_KINDS
    chatbot_count = sum(
        1 for ex in examples if normalize_kind(ex.expected_kind) == KIND_CHATBOT
    )
    agent_count = sum(
        1 for ex in examples if normalize_kind(ex.expected_kind) == KIND_AGENT
    )
    assert chatbot_count >= 2
    assert agent_count >= 2
    for ex in examples:
        validate_scenario(ex)


def test_render_examples_report() -> None:
    report = render_examples_report(default_scenarios())
    assert "标签：chatbot" in report or "标签：agent" in report
    assert "目标：" in report
    assert "理由：" in report
    with pytest.raises(ValueError, match="empty"):
        render_examples_report([])
