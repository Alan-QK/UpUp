"""Day 68 测试：Reflection 反思纠错。"""

from __future__ import annotations

import pytest

from reflection import (
    DECISION_ABORT,
    DECISION_ACCEPT,
    DECISION_RETRY,
    DECISION_REVISE,
    ISSUE_FAILED_STATUS,
    ISSUE_SKIPPED_STATUS,
    ISSUE_TOO_SHORT,
    MIN_OBS_LEN,
    PASS_SCORE,
    REQUIRED_REPORT_SECTIONS,
    STATUS_DONE,
    STATUS_FAILED,
    STATUS_SKIPPED,
    STOP_COMPLETED,
    STOP_FAILED,
    Critique,
    RunSnapshot,
    StepSnapshot,
    apply_retry,
    build_demo_runs,
    build_sample_failed_run,
    build_sample_good_run,
    build_sample_weak_run,
    critique_run,
    critique_step,
    improve_step,
    pick_overall_decision,
    render_reflection,
    render_reflection_report,
    run_demo_reflection,
    run_reflection,
    score_step,
    summarize_reflection,
)


def test_score_step_statuses() -> None:
    done_ok = StepSnapshot(
        "S1",
        "澄清",
        "clarify",
        STATUS_DONE,
        "已澄清目标并写清范围、受众与成功标准。",
    )
    score, issues = score_step(done_ok)
    assert score >= PASS_SCORE
    assert issues == ()

    short = StepSnapshot("S2", "检索", "research", STATUS_DONE, "短")
    score, issues = score_step(short)
    assert score < PASS_SCORE
    assert ISSUE_TOO_SHORT in issues
    assert len(short.observation) < MIN_OBS_LEN

    failed = StepSnapshot(
        "S3",
        "检索",
        "research",
        STATUS_FAILED,
        "",
        "RuntimeError: boom",
    )
    score, issues = score_step(failed)
    assert score == 0.0
    assert ISSUE_FAILED_STATUS in issues

    skipped = StepSnapshot("S4", "交付", "deliver", STATUS_SKIPPED, "", "deps")
    score, issues = score_step(skipped)
    assert score < PASS_SCORE
    assert ISSUE_SKIPPED_STATUS in issues


def test_critique_step_decisions() -> None:
    ok = critique_step(
        StepSnapshot(
            "S1",
            "澄清",
            "clarify",
            STATUS_DONE,
            "已澄清目标并写清范围、受众与成功标准。",
        )
    )
    assert ok.decision == DECISION_ACCEPT

    weak = critique_step(StepSnapshot("S2", "检索", "research", STATUS_DONE, "短"))
    assert weak.decision == DECISION_RETRY
    assert weak.retry_hint

    skipped = critique_step(
        StepSnapshot("S3", "分析", "analyze", STATUS_SKIPPED, "", "deps")
    )
    assert skipped.decision == DECISION_REVISE


def test_pick_overall_priority() -> None:
    cs = (
        Critique("a", 0.9, (), DECISION_ACCEPT, "ok"),
        Critique("b", 0.2, (), DECISION_RETRY, "r", "h"),
        Critique("c", 0.1, (), DECISION_REVISE, "v"),
    )
    assert pick_overall_decision(cs) == DECISION_REVISE
    assert (
        pick_overall_decision(
            (
                Critique("a", 0.9, (), DECISION_ACCEPT, "ok"),
                Critique("b", 0.2, (), DECISION_RETRY, "r", "h"),
            )
        )
        == DECISION_RETRY
    )
    with pytest.raises(ValueError):
        pick_overall_decision(())


def test_improve_and_apply_retry() -> None:
    step = StepSnapshot("S1", "检索", "research", STATUS_FAILED, "", "boom")
    fixed = improve_step(step, hint="换关键词")
    assert fixed.status == STATUS_DONE
    assert fixed.error == ""
    assert len(fixed.observation) >= MIN_OBS_LEN
    assert "换关键词" in fixed.observation

    run = RunSnapshot(
        goal="修复薄弱观察",
        stop_reason=STOP_COMPLETED,
        has_deliverable=False,
        steps=(
            StepSnapshot("S1", "澄清", "clarify", STATUS_DONE, "短"),
            StepSnapshot("S2", "交付", "deliver", STATUS_DONE, "草稿"),
        ),
    )
    critiques = (critique_step(run.steps[0]), critique_step(run.steps[1]))
    new_run = apply_retry(run, critiques)
    assert all(s.status == STATUS_DONE for s in new_run.steps)
    assert all(len(s.observation) >= MIN_OBS_LEN for s in new_run.steps)


def test_good_run_accepts_immediately() -> None:
    result = run_reflection(build_sample_good_run())
    assert result.final_decision == DECISION_ACCEPT
    assert result.retries_used == 0
    assert len(result.rounds) == 1
    stats = summarize_reflection(result)
    assert stats["final_decision"] == DECISION_ACCEPT
    assert stats["final_has_deliverable"] is True


def test_weak_run_retries_then_accepts() -> None:
    result = run_reflection(build_sample_weak_run(), max_rounds=3)
    assert result.final_decision == DECISION_ACCEPT
    assert result.retries_used >= 1
    assert result.final_run is not None
    assert result.final_run.has_deliverable is True


def test_failed_cascade_revises() -> None:
    result = run_reflection(build_sample_failed_run(), max_rounds=3)
    assert result.final_decision == DECISION_REVISE
    # 级联跳过不应靠盲重试解决
    run_c = critique_run(build_sample_failed_run())
    assert run_c.decision in {DECISION_REVISE, DECISION_RETRY}


def test_single_failure_can_retry() -> None:
    run = RunSnapshot(
        goal="单步失败可重试",
        stop_reason=STOP_FAILED,
        has_deliverable=False,
        steps=(
            StepSnapshot(
                "S1",
                "澄清",
                "clarify",
                STATUS_DONE,
                "已澄清目标并明确范围与受众标准。",
            ),
            StepSnapshot(
                "S2",
                "检索",
                "research",
                STATUS_FAILED,
                "",
                "RuntimeError: boom",
            ),
        ),
    )
    result = run_reflection(run, max_rounds=3)
    assert result.final_decision == DECISION_ACCEPT
    assert result.retries_used >= 1
    assert result.final_run is not None
    assert result.final_run.steps[1].status == STATUS_DONE


def test_max_rounds_aborts() -> None:
    result = run_reflection(build_sample_weak_run(), max_rounds=1)
    assert result.final_decision == DECISION_ABORT
    assert result.retries_used == 0  # 最后一轮需 retry 时不 apply
    with pytest.raises(ValueError):
        run_reflection(build_sample_good_run(), max_rounds=0)
    with pytest.raises(TypeError):
        run_reflection(build_sample_good_run(), max_rounds=True)  # type: ignore[arg-type]


def test_samples_demo_report() -> None:
    good = build_sample_good_run()
    weak = build_sample_weak_run()
    failed = build_sample_failed_run()
    assert good.stop_reason == STOP_COMPLETED
    assert good.has_deliverable is True
    assert weak.has_deliverable is False
    assert failed.stop_reason == STOP_FAILED
    assert any(s.status == STATUS_SKIPPED for s in failed.steps)

    demos = build_demo_runs()
    assert len(demos) >= 3
    results = run_demo_reflection()
    assert len(results) >= 3

    result = run_reflection(good)
    md = render_reflection(result)
    assert good.goal in md
    assert DECISION_ACCEPT in md

    report = render_reflection_report()
    for title in REQUIRED_REPORT_SECTIONS:
        assert f"## {title}" in report
