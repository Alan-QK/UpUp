"""Day 69 测试：Agent 状态机。"""

from __future__ import annotations

import pytest

from state_machine import (
    DECISION_TO_EVENT,
    EVENT_DECISION_ABORT,
    EVENT_DECISION_ACCEPT,
    EVENT_DECISION_RETRY,
    EVENT_DECISION_REVISE,
    EVENT_EXECUTION_FINISHED,
    EVENT_GOAL_RECEIVED,
    EVENT_HITL_APPROVED,
    EVENT_HITL_REJECTED,
    EVENT_NEED_HITL,
    EVENT_PLAN_READY,
    EVENT_RESET,
    HITL_RESUME_DEFAULT,
    IllegalTransitionError,
    REQUIRED_REPORT_SECTIONS,
    STATE_ABORTED,
    STATE_AWAITING_HITL,
    STATE_DONE,
    STATE_EXECUTING,
    STATE_IDLE,
    STATE_PLANNING,
    STATE_REFLECTING,
    AgentStateMachine,
    apply_events,
    build_demo_machines,
    build_transition_map,
    can_transition,
    default_transitions,
    list_events_from,
    lookup_transition,
    map_reflection_decision,
    render_mermaid,
    render_state_machine_report,
    render_trace,
    simulate_abort_on_reflect,
    simulate_happy_path,
    simulate_hitl_approve,
    simulate_hitl_reject,
    simulate_retry_then_accept,
    simulate_revise_loop,
    summarize_machine,
)


def test_default_transitions_cover_main_and_loops() -> None:
    mapping = build_transition_map()
    assert mapping[(STATE_IDLE, EVENT_GOAL_RECEIVED)].target == STATE_PLANNING
    assert mapping[(STATE_PLANNING, EVENT_PLAN_READY)].target == STATE_EXECUTING
    assert (
        mapping[(STATE_EXECUTING, EVENT_EXECUTION_FINISHED)].target == STATE_REFLECTING
    )
    assert mapping[(STATE_REFLECTING, EVENT_DECISION_ACCEPT)].target == STATE_DONE
    assert mapping[(STATE_REFLECTING, EVENT_DECISION_RETRY)].target == STATE_EXECUTING
    assert mapping[(STATE_REFLECTING, EVENT_DECISION_REVISE)].target == STATE_PLANNING
    assert mapping[(STATE_REFLECTING, EVENT_DECISION_ABORT)].target == STATE_ABORTED
    assert mapping[(STATE_AWAITING_HITL, EVENT_HITL_REJECTED)].target == STATE_ABORTED
    assert mapping[(STATE_DONE, EVENT_RESET)].target == STATE_IDLE
    # hitl_approved 不进静态表
    assert (STATE_AWAITING_HITL, EVENT_HITL_APPROVED) not in mapping
    assert len(default_transitions()) >= 10


def test_can_transition_and_illegal() -> None:
    assert can_transition(STATE_IDLE, EVENT_GOAL_RECEIVED) is True
    assert can_transition(STATE_IDLE, EVENT_PLAN_READY) is False
    assert can_transition(STATE_AWAITING_HITL, EVENT_HITL_APPROVED) is True

    with pytest.raises(IllegalTransitionError):
        lookup_transition(STATE_IDLE, EVENT_PLAN_READY)

    with pytest.raises(IllegalTransitionError):
        lookup_transition(STATE_AWAITING_HITL, EVENT_HITL_APPROVED)

    events = list_events_from(STATE_REFLECTING)
    assert EVENT_DECISION_ACCEPT in events
    assert EVENT_DECISION_RETRY in events
    assert events == sorted(events)


def test_map_reflection_decision() -> None:
    for decision, event in DECISION_TO_EVENT.items():
        assert map_reflection_decision(decision) == event
        assert map_reflection_decision(decision.upper()) == event
    with pytest.raises(ValueError):
        map_reflection_decision("noop")


def test_happy_path_and_snapshot() -> None:
    m = simulate_happy_path()
    assert m.state == STATE_DONE
    assert m.is_terminal() is True
    snap = m.snapshot()
    assert snap["path"] == [
        STATE_IDLE,
        STATE_PLANNING,
        STATE_EXECUTING,
        STATE_REFLECTING,
        STATE_DONE,
    ]
    sm = summarize_machine(m)
    assert sm["final_state"] == STATE_DONE
    assert sm["events"][0] == EVENT_GOAL_RECEIVED


def test_retry_revise_abort_simulations() -> None:
    retry = simulate_retry_then_accept()
    assert retry.state == STATE_DONE
    assert EVENT_DECISION_RETRY in [r.event for r in retry.history]
    assert [r.to_state for r in retry.history].count(STATE_EXECUTING) == 2

    revise = simulate_revise_loop()
    assert revise.state == STATE_DONE
    assert EVENT_DECISION_REVISE in [r.event for r in revise.history]
    assert STATE_PLANNING in [r.to_state for r in revise.history][1:]

    aborted = simulate_abort_on_reflect()
    assert aborted.state == STATE_ABORTED
    assert aborted.is_terminal() is True


def test_hitl_approve_and_reject() -> None:
    ok = simulate_hitl_approve()
    assert ok.state == STATE_DONE
    assert ok.hitl_resume is None
    assert EVENT_HITL_APPROVED in [r.event for r in ok.history]
    # planning 人审后应恢复到 executing
    assert HITL_RESUME_DEFAULT[STATE_PLANNING] == STATE_EXECUTING

    rejected = simulate_hitl_reject()
    assert rejected.state == STATE_ABORTED
    assert rejected.hitl_resume is None

    m = AgentStateMachine()
    m.send(EVENT_GOAL_RECEIVED)
    m.send(EVENT_NEED_HITL)
    assert m.state == STATE_AWAITING_HITL
    assert m.hitl_resume == STATE_EXECUTING
    m.send(EVENT_HITL_APPROVED)
    assert m.state == STATE_EXECUTING
    assert m.hitl_resume is None


def test_illegal_send_and_reset() -> None:
    m = AgentStateMachine()
    with pytest.raises(IllegalTransitionError):
        m.send(EVENT_PLAN_READY)

    done = simulate_happy_path()
    done.send(EVENT_RESET)
    assert done.state == STATE_IDLE
    assert done.hitl_resume is None


def test_send_decision_and_apply_events() -> None:
    m = apply_events(
        [EVENT_GOAL_RECEIVED, EVENT_PLAN_READY, EVENT_EXECUTION_FINISHED]
    )
    assert m.state == STATE_REFLECTING
    m.send_decision("accept")
    assert m.state == STATE_DONE


def test_render_mermaid_and_trace() -> None:
    diagram = render_mermaid()
    assert "stateDiagram-v2" in diagram
    assert "[*] --> idle" in diagram
    assert f"{STATE_IDLE} --> {STATE_PLANNING}: {EVENT_GOAL_RECEIVED}" in diagram
    assert f"{STATE_REFLECTING} --> {STATE_EXECUTING}: {EVENT_DECISION_RETRY}" in diagram
    # 动态恢复边
    assert f"{STATE_AWAITING_HITL} --> {STATE_EXECUTING}: {EVENT_HITL_APPROVED}" in diagram
    assert f"{STATE_AWAITING_HITL} --> {STATE_REFLECTING}: {EVENT_HITL_APPROVED}" in diagram
    assert f"{STATE_AWAITING_HITL} --> {STATE_DONE}: {EVENT_HITL_APPROVED}" in diagram

    trace = render_trace(simulate_happy_path())
    assert "goal_received" in trace
    assert STATE_DONE in trace or "`done`" in trace


def test_demo_and_report() -> None:
    demos = build_demo_machines()
    assert len(demos) >= 5
    finals = {m.state for m in demos}
    assert STATE_DONE in finals
    assert STATE_ABORTED in finals

    report = render_state_machine_report(demos)
    for title in REQUIRED_REPORT_SECTIONS:
        assert f"## {title}" in report
    assert "stateDiagram-v2" in report
