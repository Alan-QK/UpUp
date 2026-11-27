"""Day 66 测试：任务分解 Planner。"""

from __future__ import annotations

import pytest

from planner import (
    COMPLEXITY_COMPLEX,
    COMPLEXITY_MEDIUM,
    COMPLEXITY_SIMPLE,
    DEFAULT_MAX_STEPS,
    GOAL_KIND_CODING,
    GOAL_KIND_GENERIC,
    GOAL_KIND_OPS,
    GOAL_KIND_RESEARCH,
    GOAL_KIND_WRITING,
    MAX_MAX_STEPS,
    MIN_GOAL_LEN,
    MIN_MAX_STEPS,
    REQUIRED_REPORT_SECTIONS,
    Plan,
    PlanStep,
    STEP_KIND_CLARIFY,
    build_demo_goals,
    classify_goal,
    estimate_complexity,
    normalize_goal,
    plan_from_goal,
    render_plan,
    render_planner_report,
    run_demo_planner,
    summarize_plans,
)


def test_normalize_goal() -> None:
    assert normalize_goal("  调研   Agent   框架  ") == "调研 Agent 框架"
    with pytest.raises(TypeError):
        normalize_goal(123)  # type: ignore[arg-type]


def test_classify_goal_priority() -> None:
    assert classify_goal("实现一个重试客户端") == GOAL_KIND_CODING
    assert classify_goal("写一份记忆系统设计文档") == GOAL_KIND_WRITING
    assert classify_goal("部署 staging 环境并监控健康状态") == GOAL_KIND_OPS
    assert classify_goal("调研 LangGraph 与自研状态机") == GOAL_KIND_RESEARCH
    assert classify_goal("整理本周学习笔记") == GOAL_KIND_GENERIC
    with pytest.raises(ValueError):
        classify_goal("hi")


def test_estimate_complexity() -> None:
    assert estimate_complexity("写测试", 3) == COMPLEXITY_SIMPLE
    assert (
        estimate_complexity("调研 A 并且对比 B 然后给出完整端到端方案", 5)
        == COMPLEXITY_COMPLEX
    )
    assert estimate_complexity("实现带缓存的检索模块", 5) == COMPLEXITY_MEDIUM


def test_plan_from_goal_basic_chain() -> None:
    plan = plan_from_goal("调研向量数据库选型")
    assert isinstance(plan, Plan)
    assert plan.goal_kind == GOAL_KIND_RESEARCH
    assert plan.strategy == "heuristic:research"
    assert len(plan.steps) >= MIN_MAX_STEPS
    assert plan.steps[0].id == "S1"
    assert plan.steps[0].depends_on == ()
    assert plan.steps[0].kind == STEP_KIND_CLARIFY
    if len(plan.steps) > 1:
        assert plan.steps[1].depends_on == ("S1",)
        assert plan.steps[1].id == "S2"


def test_plan_short_goal_truncates_to_three() -> None:
    plan = plan_from_goal("实现缓存", max_steps=DEFAULT_MAX_STEPS)
    assert plan.goal_kind == GOAL_KIND_CODING
    assert len(plan.steps) == 3


def test_plan_respects_max_steps_and_rejects_bad() -> None:
    plan = plan_from_goal(
        "调研并且对比并且评估完整端到端多智能体方案然后给出建议",
        max_steps=4,
    )
    assert len(plan.steps) == 4
    with pytest.raises(ValueError):
        plan_from_goal("hi")
    with pytest.raises(ValueError):
        plan_from_goal("实现一个模块", max_steps=2)
    with pytest.raises(TypeError):
        plan_from_goal("实现一个模块", max_steps=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        plan_from_goal("实现一个模块", max_steps=MAX_MAX_STEPS + 1)


def test_plan_step_validation() -> None:
    with pytest.raises(ValueError):
        PlanStep(id="", title="x", detail="d", kind=STEP_KIND_CLARIFY)
    with pytest.raises(ValueError):
        Plan(
            goal="合法目标文本",
            steps=(
                PlanStep(
                    id="S1",
                    title="a",
                    detail="d",
                    kind=STEP_KIND_CLARIFY,
                    depends_on=("S9",),
                ),
            ),
            goal_kind=GOAL_KIND_GENERIC,
            strategy="heuristic:generic",
            complexity=COMPLEXITY_SIMPLE,
        )


def test_render_plan_contains_meta() -> None:
    plan = plan_from_goal("写一份 Agent 评测报告")
    md = render_plan(plan)
    assert plan.goal in md
    assert plan.goal_kind in md
    assert "S1" in md
    assert "## 步骤" in md


def test_demo_and_summary() -> None:
    goals = build_demo_goals()
    assert any(len(normalize_goal(g)) < MIN_GOAL_LEN for g in goals if isinstance(g, str))
    plans = run_demo_planner(goals)
    assert len(plans) >= 3
    stats = summarize_plans(plans)
    assert stats["plan_count"] == len(plans)
    assert stats["total_steps"] >= len(plans) * MIN_MAX_STEPS
    assert "by_kind" in stats and "by_complexity" in stats


def test_report_sections() -> None:
    report = render_planner_report()
    for title in REQUIRED_REPORT_SECTIONS:
        assert f"## {title}" in report
