"""Day 60 tool-agent tests（纯本地，无网络）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from hitl import AlwaysApprove, ConfirmationDecision, ScriptedConfirmHook
from mock_llm import MockLLM, assistant_text, assistant_tool_call
from tool_agent import (
    REQUIRED_ACCEPTANCE_KEYS,
    REQUIRED_REPORT_SECTIONS,
    STOP_FINAL,
    STOP_MAX_STEPS,
    ToolAgent,
    ToolAgentError,
)
from tools import FAKE_HTTP_PAGES

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "sample_workspace"


def test_from_workspace_lists_tools() -> None:
    agent = ToolAgent.from_workspace(WORKSPACE)
    enabled = [
        s.name
        for s in agent.catalog.values()
        if s.enabled and s.risk != "blocked"
    ]
    assert len(enabled) >= 3
    for name in ("get_time", "calculate", "list_files", "read_file", "http_get"):
        assert name in enabled
    assert "shell_exec" in agent.catalog
    assert agent.catalog["shell_exec"].risk == "blocked"


def test_empty_goal_raises() -> None:
    agent = ToolAgent.from_workspace(WORKSPACE)
    with pytest.raises(ToolAgentError):
        agent.run("  ", llm=MockLLM([assistant_text("x")]))


def test_scenario_calc_time() -> None:
    agent = ToolAgent.from_workspace(WORKSPACE, confirm_hook=AlwaysApprove())
    result = agent.run_scenario("calc_time")
    assert result.stopped_reason == STOP_FINAL
    assert result.llm_calls == 3
    assert any("calculate" in step.tool_names for step in result.steps)
    assert any("get_time" in step.tool_names for step in result.steps)
    # observation 中应含计算结果 84
    joined = " ".join(obs for step in result.steps for obs in step.observations)
    assert "84" in joined


def test_scenario_read_notes() -> None:
    agent = ToolAgent.from_workspace(WORKSPACE)
    result = agent.run_scenario("read_notes")
    assert result.stopped_reason == STOP_FINAL
    joined = " ".join(obs for step in result.steps for obs in step.observations)
    assert "notes.txt" in joined
    assert "Guard" in joined or "HITL" in joined or "Trace" in joined


def test_scenario_http_docs() -> None:
    agent = ToolAgent.from_workspace(WORKSPACE)
    result = agent.run_scenario("http_docs")
    assert result.stopped_reason == STOP_FINAL
    joined = " ".join(obs for step in result.steps for obs in step.observations)
    assert "Python" in joined or FAKE_HTTP_PAGES["docs.python.org"][:10] in joined


def test_refund_approve_has_side_effect() -> None:
    agent = ToolAgent.from_workspace(WORKSPACE)
    result = agent.run_scenario("refund_approve")
    assert result.stopped_reason == STOP_FINAL
    assert "ORD-1001" in result.refunded_orders
    assert len(result.confirmations) == 1
    assert result.confirmations[0].decision.decision == "approve"


def test_refund_reject_no_side_effect() -> None:
    agent = ToolAgent.from_workspace(WORKSPACE)
    result = agent.run_scenario("refund_reject")
    assert result.stopped_reason == STOP_FINAL
    assert "ORD-1001" not in result.refunded_orders
    assert len(result.confirmations) == 1
    assert result.confirmations[0].decision.decision == "reject"
    joined = " ".join(obs for step in result.steps for obs in step.observations)
    assert "REJECTED_BY_USER" in joined


def test_blocked_shell_never_runs() -> None:
    agent = ToolAgent.from_workspace(WORKSPACE)
    result = agent.run_scenario("blocked_shell")
    assert result.stopped_reason == STOP_FINAL
    assert result.confirmations == ()
    joined = " ".join(obs for step in result.steps for obs in step.observations)
    assert "denied" in joined


def test_max_steps_stop() -> None:
    agent = ToolAgent.from_workspace(WORKSPACE, max_steps=2)
    result = agent.run_scenario("max_steps")
    assert result.stopped_reason == STOP_MAX_STEPS
    assert result.llm_calls == 2
    assert all(step.kind == "action" for step in result.steps)


def test_format_trace_and_report() -> None:
    agent = ToolAgent.from_workspace(WORKSPACE)
    result = agent.run_scenario("calc_time")
    md = agent.format_trace(result)
    assert md.startswith("# Tool-Agent Trace\n")
    assert "stopped_reason" in md

    report = agent.render_acceptance_report()
    for section in REQUIRED_REPORT_SECTIONS:
        assert f"## {section}" in report

    checklist = agent.acceptance_checklist()
    assert set(checklist) == set(REQUIRED_ACCEPTANCE_KEYS)
    assert all(checklist.values())


def test_path_escape_denied_via_tool() -> None:
    agent = ToolAgent.from_workspace(WORKSPACE, confirm_hook=AlwaysApprove())
    llm = MockLLM(
        [
            assistant_tool_call(
                "read_file",
                {"relative_path": "../secrets.txt"},
                call_id="c1",
                thought="越界",
            ),
            assistant_text("无法读取。"),
        ]
    )
    result = agent.run("读上级目录", llm=llm)
    assert result.stopped_reason == STOP_FINAL
    joined = " ".join(obs for step in result.steps for obs in step.observations)
    assert "ok\": false" in joined.replace(" ", "") or '"ok": false' in joined


def test_scripted_timeout_on_refund() -> None:
    agent = ToolAgent.from_workspace(
        WORKSPACE,
        confirm_hook=ScriptedConfirmHook([]),  # 耗尽 → timeout
    )
    llm = MockLLM(
        [
            assistant_tool_call(
                "refund_order",
                {"order_id": "ORD-1001"},
                call_id="c1",
                thought="退款",
            ),
            assistant_text("确认超时，未退款。"),
        ]
    )
    result = agent.run("退款 ORD-1001", llm=llm)
    assert "ORD-1001" not in result.refunded_orders
    assert result.confirmations[0].decision.decision == "timeout"
    joined = " ".join(obs for step in result.steps for obs in step.observations)
    assert "CONFIRM_TIMEOUT" in joined
