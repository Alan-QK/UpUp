"""Day 70 测试：多步研究任务。"""

from __future__ import annotations

import pytest

from research_pipeline import (
    DECISION_ACCEPT,
    DECISION_RETRY,
    REQUIRED_REPORT_SECTIONS,
    STATE_DONE,
    STATE_EXECUTING,
    STATE_PLANNING,
    STATE_REFLECTING,
    STATUS_DONE,
    STATUS_FAILED,
    STATUS_SKIPPED,
    STOP_COMPLETED,
    STOP_FAILED,
    build_demo_runs,
    build_research_plan,
    critique_trace,
    execute_plan,
    normalize_goal,
    render_execution,
    render_plan,
    render_research_report,
    run_research_task,
    summarize_run,
)


def test_normalize_and_plan_basics() -> None:
    assert normalize_goal("  调研  向量库  ") == "调研 向量库"
    with pytest.raises(ValueError):
        build_research_plan("hi")

    plan = build_research_plan("调研向量数据库选型")
    assert len(plan.steps) >= 3
    assert plan.strategy == "research_template"
    assert plan.steps[0].id == "S1"
    assert plan.steps[1].depends_on == ("S1",)
    assert all(s.kind for s in plan.steps)

    short = build_research_plan("调研缓存方案对比", max_steps=3)
    assert len(short.steps) == 3
    assert short.steps[-1].kind == "deliver"


def test_execute_happy_and_fail() -> None:
    plan = build_research_plan("评估本地向量检索方案")
    ok = execute_plan(plan)
    assert ok.stop_reason == STOP_COMPLETED
    assert ok.deliverable.strip()
    assert all(r.status == STATUS_DONE for r in ok.results)
    assert len(ok.results) == len(plan.steps)

    bad = execute_plan(plan, fail_step_id="S2")
    assert bad.stop_reason == STOP_FAILED
    assert bad.results[1].status == STATUS_FAILED
    assert any(r.status == STATUS_SKIPPED for r in bad.results[2:])
    assert not bad.deliverable.strip()


def test_critique_accept_and_retry() -> None:
    plan = build_research_plan("对比开源向量库")
    ok = execute_plan(plan)
    c_ok = critique_trace(ok)
    assert c_ok.decision == DECISION_ACCEPT

    bad = execute_plan(plan, fail_step_id="S2")
    c_bad = critique_trace(bad)
    assert c_bad.decision == DECISION_RETRY
    assert c_bad.weak_step_id == "S2"


def test_run_happy_path_state_machine() -> None:
    run = run_research_task("调研向量数据库选型")
    assert run.decision == DECISION_ACCEPT
    assert run.rounds == 1
    assert run.trace.stop_reason == STOP_COMPLETED
    assert run.trace.deliverable.strip()
    assert STATE_PLANNING in run.state_path
    assert STATE_EXECUTING in run.state_path
    assert STATE_REFLECTING in run.state_path
    assert run.state_path[-1] == STATE_DONE
    assert run.state_path[0] == "idle"


def test_run_retry_after_injected_failure() -> None:
    run = run_research_task(
        "对比开源向量库与托管方案",
        inject_fail_step="S2",
        max_rounds=2,
    )
    assert run.decision == DECISION_ACCEPT
    assert run.rounds == 2
    assert len(run.critiques) == 2
    assert run.critiques[0].decision == DECISION_RETRY
    assert run.critiques[1].decision == DECISION_ACCEPT
    assert run.trace.stop_reason == STOP_COMPLETED
    assert run.state_path.count(STATE_EXECUTING) >= 2
    assert run.state_path.count(STATE_REFLECTING) >= 2


def test_abort_when_max_rounds_exhausted() -> None:
    # max_rounds=1 且注入失败 → 首轮 retry 后直接 abort
    run = run_research_task(
        "调研图数据库选型要点",
        inject_fail_step="S2",
        max_rounds=1,
    )
    assert run.decision == "abort"
    assert run.rounds == 1
    assert run.state_path[-1] == "aborted"


def test_render_and_report() -> None:
    runs = build_demo_runs()
    assert len(runs) >= 2
    plan_md = render_plan(runs[0].plan)
    assert "研究计划" in plan_md
    assert "S1" in plan_md

    exec_md = render_execution(runs[0].trace)
    assert "执行轨迹" in exec_md
    assert "deliverable" in exec_md.lower() or "Deliverable" in exec_md

    sm = summarize_run(runs[0])
    assert sm["has_deliverable"] is True
    assert isinstance(sm["state_path"], list)

    report = render_research_report(runs)
    for section in REQUIRED_REPORT_SECTIONS:
        assert f"## {section}" in report
    assert "研究计划" in report
    assert "执行轨迹" in report
