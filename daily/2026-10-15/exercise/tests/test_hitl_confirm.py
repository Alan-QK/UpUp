"""Day 59：HITL 确认钩子。"""

from __future__ import annotations

import pytest

from hitl_confirm import (
    BRANCH_APPROVE,
    BRANCH_BLOCKED,
    BRANCH_REJECT,
    BRANCH_SAFE_AUTO,
    BRANCH_TIMEOUT,
    DECISION_APPROVE,
    DECISION_REJECT,
    DECISION_TIMEOUT,
    REQUIRED_BRANCHES,
    REQUIRED_REPORT_SECTIONS,
    RISK_BLOCKED,
    RISK_CONFIRM,
    RISK_SAFE,
    STOP_FINAL,
    ConfirmationDecision,
    ConfirmationRequest,
    MockLLM,
    ScriptedConfirmHook,
    SideEffectLedger,
    assistant_final,
    assistant_tool_call,
    build_tool_catalog,
    classify_risk,
    has_tool_calls,
    hitl_execute,
    normalize_text,
    normalize_tool_name,
    order_lookup,
    parse_tool_calls,
    render_hitl_report,
    run_hitl_agent,
    run_scenario,
    scenario_responses,
)


def test_normalize_helpers() -> None:
    assert normalize_text("  a\n\tb  ") == "a b"
    assert normalize_tool_name(" Refund_Order ") == "refund_order"
    with pytest.raises(ValueError, match="name"):
        normalize_tool_name("  ")


def test_classify_risk() -> None:
    assert classify_risk("order_lookup") == RISK_SAFE
    assert classify_risk("refund_order") == RISK_CONFIRM
    assert classify_risk("shell_exec") == RISK_BLOCKED
    assert classify_risk("totally_unknown") == RISK_BLOCKED


def test_order_lookup() -> None:
    text = order_lookup("ORD-1001")
    assert "ORD-1001" in text
    assert "shipped" in text
    with pytest.raises(ValueError):
        order_lookup(" ")
    with pytest.raises(KeyError):
        order_lookup("ORD-9999")


def test_build_tool_catalog_risks() -> None:
    ledger = SideEffectLedger()
    catalog = build_tool_catalog(ledger)
    assert set(catalog.keys()) == {
        "order_lookup",
        "get_time",
        "refund_order",
        "delete_account",
    }
    assert catalog["order_lookup"].risk == RISK_SAFE
    assert catalog["refund_order"].risk == RISK_CONFIRM
    assert "shell_exec" not in catalog


def test_message_factories() -> None:
    final = assistant_final("你好")
    assert has_tool_calls(final) is False
    tool = assistant_tool_call("c1", "refund_order", {"order_id": "ORD-2001"})
    assert has_tool_calls(tool) is True
    parsed = parse_tool_calls(tool)
    assert parsed[0][1] == "refund_order"
    assert parsed[0][2] == {"order_id": "ORD-2001"}


def test_scripted_confirm_hook() -> None:
    hook = ScriptedConfirmHook([DECISION_APPROVE, "reject"])
    req = ConfirmationRequest(
        tool_name="refund_order",
        args={"order_id": "ORD-2001"},
        reason="test",
        risk=RISK_CONFIRM,
    )
    first = hook(req)
    assert first.decision == DECISION_APPROVE
    second = hook(req)
    assert second.decision == DECISION_REJECT
    third = hook(req)
    assert third.decision == DECISION_TIMEOUT
    assert len(hook.requests) == 3


def test_hitl_execute_safe_no_confirmation() -> None:
    ledger = SideEffectLedger()
    catalog = build_tool_catalog(ledger)
    confirmations: list = []
    hook = ScriptedConfirmHook([DECISION_APPROVE])
    obs = hitl_execute(
        "order_lookup",
        {"order_id": "ORD-1001"},
        catalog=catalog,
        confirm_hook=hook,
        confirmations=confirmations,
    )
    assert "ORD-1001" in obs
    assert confirmations == []
    assert hook.requests == []


def test_hitl_execute_approve_records_side_effect() -> None:
    ledger = SideEffectLedger()
    catalog = build_tool_catalog(ledger)
    confirmations: list = []
    hook = ScriptedConfirmHook([DECISION_APPROVE])
    obs = hitl_execute(
        "refund_order",
        {"order_id": "ORD-2001"},
        catalog=catalog,
        confirm_hook=hook,
        confirmations=confirmations,
    )
    assert "已退款" in obs or "退款" in obs
    assert ledger.refunds == ["ORD-2001"]
    assert len(confirmations) == 1
    assert confirmations[0].decision.decision == DECISION_APPROVE


def test_hitl_execute_reject_no_side_effect() -> None:
    ledger = SideEffectLedger()
    catalog = build_tool_catalog(ledger)
    confirmations: list = []
    hook = ScriptedConfirmHook([DECISION_REJECT])
    obs = hitl_execute(
        "refund_order",
        {"order_id": "ORD-2001"},
        catalog=catalog,
        confirm_hook=hook,
        confirmations=confirmations,
    )
    assert "rejected" in obs.lower()
    assert ledger.refunds == []
    assert len(confirmations) == 1


def test_hitl_execute_timeout_no_side_effect() -> None:
    ledger = SideEffectLedger()
    catalog = build_tool_catalog(ledger)
    confirmations: list = []
    hook = ScriptedConfirmHook([DECISION_TIMEOUT])
    obs = hitl_execute(
        "delete_account",
        {"account_id": "ACC-9"},
        catalog=catalog,
        confirm_hook=hook,
        confirmations=confirmations,
    )
    assert "timeout" in obs.lower()
    assert ledger.deletions == []
    assert len(confirmations) == 1


def test_hitl_execute_blocked_skips_hook() -> None:
    ledger = SideEffectLedger()
    catalog = build_tool_catalog(ledger)
    confirmations: list = []
    hook = ScriptedConfirmHook([DECISION_APPROVE])
    obs = hitl_execute(
        "shell_exec",
        {"cmd": "rm -rf /"},
        catalog=catalog,
        confirm_hook=hook,
        confirmations=confirmations,
    )
    assert "denied" in obs.lower()
    assert "block" in obs.lower()
    assert confirmations == []
    assert hook.requests == []


def test_run_safe_auto_branch() -> None:
    result = run_scenario(BRANCH_SAFE_AUTO)
    assert result.stopped_reason == STOP_FINAL
    assert result.confirmations == ()
    assert any("ORD-1001" in obs for obs in result.steps[0].observations)


def test_run_approve_branch() -> None:
    result = run_scenario(BRANCH_APPROVE)
    assert result.stopped_reason == STOP_FINAL
    assert result.ledger.refunds == ["ORD-2001"]
    assert len(result.confirmations) == 1
    assert result.confirmations[0].decision.decision == DECISION_APPROVE
    assert any("退款" in obs or "refund" in obs.lower() for obs in result.steps[0].observations)


def test_run_reject_branch() -> None:
    result = run_scenario(BRANCH_REJECT)
    assert result.stopped_reason == STOP_FINAL
    assert result.ledger.refunds == []
    assert len(result.confirmations) == 1
    assert any("rejected" in obs.lower() for obs in result.steps[0].observations)


def test_run_timeout_branch() -> None:
    result = run_scenario(BRANCH_TIMEOUT)
    assert result.stopped_reason == STOP_FINAL
    assert result.ledger.deletions == []
    assert len(result.confirmations) == 1
    assert any("timeout" in obs.lower() for obs in result.steps[0].observations)


def test_run_blocked_branch() -> None:
    result = run_scenario(BRANCH_BLOCKED)
    assert result.stopped_reason == STOP_FINAL
    assert result.confirmations == ()
    assert any("denied" in obs.lower() for obs in result.steps[0].observations)


def test_run_hitl_agent_rejects_empty_goal() -> None:
    with pytest.raises(ValueError):
        run_hitl_agent("  ", MockLLM([assistant_final("x")]))


def test_run_hitl_agent_rejects_bad_max_steps() -> None:
    with pytest.raises(ValueError):
        run_hitl_agent("goal", MockLLM([assistant_final("x")]), max_steps=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        run_hitl_agent("goal", MockLLM([assistant_final("x")]), max_steps=0)


def test_scenario_responses_unknown() -> None:
    with pytest.raises(ValueError, match="branch"):
        scenario_responses("not-a-branch")
    assert REQUIRED_BRANCHES == {
        BRANCH_SAFE_AUTO,
        BRANCH_APPROVE,
        BRANCH_REJECT,
        BRANCH_TIMEOUT,
        BRANCH_BLOCKED,
    }


def test_render_hitl_report() -> None:
    report = render_hitl_report()
    for section in REQUIRED_REPORT_SECTIONS:
        assert f"## {section}" in report
    assert "HITL" in report or "确认" in report
    assert "Day 60" in report or "tool-agent" in report


def test_confirm_decision_type() -> None:
    d = ConfirmationDecision(decision=DECISION_APPROVE, note="ok")
    assert d.decision == DECISION_APPROVE
    assert d.note == "ok"
