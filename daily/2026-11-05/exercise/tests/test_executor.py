"""Day 67 测试：Plan-and-Execute 执行器。"""

from __future__ import annotations

import pytest

from executor import (
    COMPLEXITY_MEDIUM,
    GOAL_KIND_CODING,
    GOAL_KIND_RESEARCH,
    KIND_TO_TOOL,
    REQUIRED_REPORT_SECTIONS,
    REQUIRED_TOOLS,
    STATUS_DONE,
    STATUS_FAILED,
    STATUS_SKIPPED,
    STEP_KIND_ANALYZE,
    STEP_KIND_CLARIFY,
    STEP_KIND_DELIVER,
    STEP_KIND_RESEARCH,
    STOP_BLOCKED,
    STOP_COMPLETED,
    STOP_FAILED,
    STOP_MAX_STEPS,
    Plan,
    PlanStep,
    StepResult,
    build_demo_plans,
    build_sample_plan,
    default_tool_registry,
    deps_satisfied,
    execute_plan,
    invoke_tool,
    kind_to_tool_name,
    render_execution,
    render_executor_report,
    run_demo_executor,
    summarize_execution,
)


def _chain_plan() -> Plan:
    return build_sample_plan(goal="调研向量数据库选型", goal_kind=GOAL_KIND_RESEARCH)


def test_kind_to_tool_name() -> None:
    assert kind_to_tool_name(STEP_KIND_CLARIFY) == "clarify_goal"
    assert kind_to_tool_name(STEP_KIND_RESEARCH) == "search_notes"
    assert kind_to_tool_name(STEP_KIND_DELIVER) == "write_deliverable"
    for kind, tool in KIND_TO_TOOL.items():
        assert kind_to_tool_name(kind) == tool
    with pytest.raises(ValueError):
        kind_to_tool_name("not-a-kind")


def test_default_registry_covers_required() -> None:
    reg = default_tool_registry()
    assert REQUIRED_TOOLS <= set(reg)
    boom_reg = default_tool_registry(include_boom=True)
    assert "boom" in boom_reg


def test_deps_satisfied() -> None:
    step = PlanStep(
        id="S2",
        title="收集",
        detail="d",
        kind=STEP_KIND_RESEARCH,
        depends_on=("S1",),
    )
    assert deps_satisfied(step, {}) is False
    assert (
        deps_satisfied(
            step,
            {
                "S1": StepResult(
                    step_id="S1",
                    status=STATUS_FAILED,
                    tool_name="clarify_goal",
                )
            },
        )
        is False
    )
    assert (
        deps_satisfied(
            step,
            {
                "S1": StepResult(
                    step_id="S1",
                    status=STATUS_DONE,
                    tool_name="clarify_goal",
                    observation="ok",
                )
            },
        )
        is True
    )
    root = PlanStep(id="S1", title="澄清", detail="d", kind=STEP_KIND_CLARIFY)
    assert deps_satisfied(root, {}) is True


def test_invoke_tool_and_context() -> None:
    reg = default_tool_registry()
    step = PlanStep(id="S1", title="澄清", detail="定范围", kind=STEP_KIND_CLARIFY)
    ctx: dict[str, object] = {"goal": "调研向量库", "notes": []}
    obs = invoke_tool("clarify_goal", step, ctx, reg)
    assert "调研向量库" in obs
    assert "clarified" in ctx
    with pytest.raises(KeyError):
        invoke_tool("no_such_tool", step, ctx, reg)


def test_execute_plan_happy_path() -> None:
    plan = _chain_plan()
    state = execute_plan(plan)
    assert state.stop_reason == STOP_COMPLETED
    assert state.steps_run == len(plan.steps)
    assert all(state.results[s.id].status == STATUS_DONE for s in plan.steps)
    assert state.context.get("goal") == plan.goal
    assert "deliverable" in state.context
    # 共享黑板：research 写入的 notes 应被后续分析看到
    assert isinstance(state.context.get("notes"), list)
    assert len(state.context["notes"]) >= 2  # type: ignore[arg-type]


def test_execute_plan_stop_on_failure() -> None:
    plan = Plan(
        goal="实现带失败注入的流水线",
        steps=(
            PlanStep(id="S1", title="澄清", detail="d", kind=STEP_KIND_CLARIFY),
            PlanStep(
                id="S2",
                title="爆炸",
                detail="d",
                kind=STEP_KIND_RESEARCH,
                depends_on=("S1",),
            ),
            PlanStep(
                id="S3",
                title="分析",
                detail="d",
                kind=STEP_KIND_ANALYZE,
                depends_on=("S2",),
            ),
        ),
        goal_kind=GOAL_KIND_CODING,
        strategy="heuristic:coding",
        complexity=COMPLEXITY_MEDIUM,
    )
    reg = default_tool_registry(include_boom=True)
    state = execute_plan(
        plan,
        registry=reg,
        kind_overrides={STEP_KIND_RESEARCH: "boom"},
        stop_on_failure=True,
    )
    assert state.stop_reason == STOP_FAILED
    assert state.results["S1"].status == STATUS_DONE
    assert state.results["S2"].status == STATUS_FAILED
    assert "RuntimeError" in state.results["S2"].error
    assert state.results["S3"].status == STATUS_SKIPPED


def test_execute_plan_blocked_dependency() -> None:
    # 人为制造：S2 依赖 S9（不存在于 results 的假依赖无法进 Plan 校验）
    # 改用：先失败 S1，再看 S2 因依赖未 DONE 被 skip
    plan = Plan(
        goal="测试依赖阻塞路径演示",
        steps=(
            PlanStep(id="S1", title="澄清", detail="d", kind=STEP_KIND_CLARIFY),
            PlanStep(
                id="S2",
                title="检索",
                detail="d",
                kind=STEP_KIND_RESEARCH,
                depends_on=("S1",),
            ),
        ),
        goal_kind=GOAL_KIND_RESEARCH,
        strategy="heuristic:research",
        complexity=COMPLEXITY_MEDIUM,
    )
    reg = default_tool_registry(include_boom=True)
    state = execute_plan(
        plan,
        registry=reg,
        kind_overrides={STEP_KIND_CLARIFY: "boom"},
        stop_on_failure=True,
    )
    assert state.stop_reason == STOP_FAILED
    assert state.results["S1"].status == STATUS_FAILED
    assert state.results["S2"].status == STATUS_SKIPPED


def test_execute_plan_max_steps() -> None:
    plan = _chain_plan()
    state = execute_plan(plan, max_steps=2)
    assert state.stop_reason == STOP_MAX_STEPS
    assert state.steps_run == 2
    done = [s.id for s in plan.steps if state.results[s.id].status == STATUS_DONE]
    skipped = [
        s.id for s in plan.steps if state.results[s.id].status == STATUS_SKIPPED
    ]
    assert len(done) == 2
    assert len(skipped) == len(plan.steps) - 2
    with pytest.raises(ValueError):
        execute_plan(plan, max_steps=0)
    with pytest.raises(TypeError):
        execute_plan(plan, max_steps=True)  # type: ignore[arg-type]


def test_execute_plan_stop_on_failure_false_continues() -> None:
    plan = Plan(
        goal="失败后继续跑后续独立步",
        steps=(
            PlanStep(id="S1", title="澄清", detail="d", kind=STEP_KIND_CLARIFY),
            PlanStep(
                id="S2",
                title="检索",
                detail="d",
                kind=STEP_KIND_RESEARCH,
                depends_on=("S1",),
            ),
        ),
        goal_kind=GOAL_KIND_RESEARCH,
        strategy="heuristic:research",
        complexity=COMPLEXITY_MEDIUM,
    )
    reg = default_tool_registry(include_boom=True)
    state = execute_plan(
        plan,
        registry=reg,
        kind_overrides={STEP_KIND_CLARIFY: "boom"},
        stop_on_failure=False,
    )
    # S1 failed；S2 依赖未满足 → skipped；最终 stop_reason=failed
    assert state.results["S1"].status == STATUS_FAILED
    assert state.results["S2"].status == STATUS_SKIPPED
    assert state.stop_reason in {STOP_FAILED, STOP_BLOCKED}


def test_build_sample_and_demo() -> None:
    plan = build_sample_plan()
    assert plan.steps[0].depends_on == ()
    assert plan.steps[1].depends_on == ("S1",)
    assert plan.strategy.startswith("heuristic:")
    plans = build_demo_plans()
    assert len(plans) >= 3
    kinds = {p.goal_kind for p in plans}
    assert len(kinds) >= 2


def test_render_and_summary() -> None:
    state = execute_plan(_chain_plan())
    md = render_execution(state)
    assert state.plan.goal in md
    assert "S1" in md
    assert STOP_COMPLETED in md or "`completed`" in md
    stats = summarize_execution(state)
    assert stats["steps_run"] == state.steps_run
    assert stats["has_deliverable"] is True
    assert stats["by_status"].get(STATUS_DONE) == len(state.plan.steps)


def test_report_sections() -> None:
    report = render_executor_report()
    for title in REQUIRED_REPORT_SECTIONS:
        assert f"## {title}" in report
    states = run_demo_executor()
    assert len(states) >= 3
    assert all(s.stop_reason == STOP_COMPLETED for s in states)
