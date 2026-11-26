"""Day 58：Mock LLM 单测。"""

from __future__ import annotations

import pytest

from mock_llm_agent import (
    BRANCH_BAD_ARGS,
    BRANCH_DENY,
    BRANCH_FINAL,
    BRANCH_MAX_STEPS,
    BRANCH_TOOL_OK,
    DANGEROUS_TOOL_NAMES,
    REQUIRED_BRANCHES,
    REQUIRED_REPORT_SECTIONS,
    STOP_FINAL,
    STOP_MAX_STEPS,
    MockLLM,
    assistant_final,
    assistant_tool_call,
    build_default_allowlist,
    guarded_execute,
    has_tool_calls,
    normalize_text,
    normalize_tool_name,
    order_lookup,
    parse_tool_calls,
    render_coverage_report,
    run_guarded_agent,
    run_scenario,
    scenario_responses,
    validate_args,
)


def test_normalize_helpers() -> None:
    assert normalize_text("  a\n\tb  ") == "a b"
    assert normalize_tool_name(" Order_Lookup ") == "order_lookup"
    with pytest.raises(ValueError, match="name"):
        normalize_tool_name("  ")


def test_order_lookup() -> None:
    text = order_lookup("ORD-1001")
    assert "ORD-1001" in text
    assert "shipped" in text
    with pytest.raises(ValueError):
        order_lookup(" ")
    with pytest.raises(KeyError):
        order_lookup("ORD-9999")


def test_build_default_allowlist() -> None:
    allowlist = build_default_allowlist()
    assert set(allowlist.keys()) == {"order_lookup", "get_time"}
    for name in DANGEROUS_TOOL_NAMES:
        assert name not in allowlist


def test_validate_args_basics() -> None:
    schema = {
        "type": "object",
        "properties": {"order_id": {"type": "string", "minLength": 1}},
        "required": ["order_id"],
        "additionalProperties": False,
    }
    ok, errors = validate_args({"order_id": "ORD-1"}, schema)
    assert ok is True
    assert errors == ()

    bad, errors = validate_args({}, schema)
    assert bad is False
    assert any("missing" in e.lower() for e in errors)


def test_message_factories() -> None:
    final = assistant_final("你好")
    assert final["role"] == "assistant"
    assert final["content"] == "你好"
    assert has_tool_calls(final) is False

    tool = assistant_tool_call("c1", "order_lookup", {"order_id": "ORD-1001"})
    assert has_tool_calls(tool) is True
    parsed = parse_tool_calls(tool)
    assert len(parsed) == 1
    call_id, name, args = parsed[0]
    assert call_id == "c1"
    assert name == "order_lookup"
    assert args == {"order_id": "ORD-1001"}


def test_mock_llm_records_and_exhausts() -> None:
    mock = MockLLM([assistant_final("one"), assistant_final("two")])
    assert mock.remaining == 2
    first = mock([{"role": "user", "content": "hi"}])
    assert first["content"] == "one"
    assert len(mock.calls) == 1
    assert mock.calls[0][0]["content"] == "hi"
    assert mock.remaining == 1
    mock([{"role": "user", "content": "again"}])
    assert mock.remaining == 0
    with pytest.raises(RuntimeError, match="exhausted|no more"):
        mock([{"role": "user", "content": "oops"}])


def test_guarded_execute_allow_and_deny() -> None:
    ok = guarded_execute("order_lookup", {"order_id": "ORD-1001"})
    assert "ORD-1001" in ok
    assert not ok.upper().startswith("DENIED")

    denied = guarded_execute("shell_exec", {"cmd": "rm -rf /"})
    assert "denied" in denied.lower()

    bad = guarded_execute("order_lookup", {})
    assert "denied" in bad.lower()
    assert "missing" in bad.lower()


def test_run_final_branch() -> None:
    result = run_scenario(BRANCH_FINAL)
    assert result.stopped_reason == STOP_FINAL
    assert result.llm_calls == 1
    assert result.steps[0].kind == "final"
    assert result.steps[0].observations == ()
    assert normalize_text(result.final_content)


def test_run_tool_ok_branch() -> None:
    result = run_scenario(BRANCH_TOOL_OK)
    assert result.stopped_reason == STOP_FINAL
    assert result.llm_calls == 2
    assert result.steps[0].kind == "action"
    assert any("ORD-1001" in obs for obs in result.steps[0].observations)
    assert result.steps[1].kind == "final"
    assert "ORD-1001" in result.final_content or "订单" in result.final_content or len(
        result.final_content
    ) > 0


def test_run_deny_branch() -> None:
    result = run_scenario(BRANCH_DENY)
    assert result.stopped_reason == STOP_FINAL
    assert result.llm_calls == 2
    assert any("denied" in obs.lower() for obs in result.steps[0].observations)


def test_run_bad_args_branch() -> None:
    result = run_scenario(BRANCH_BAD_ARGS)
    assert result.stopped_reason == STOP_FINAL
    assert any("denied" in obs.lower() for obs in result.steps[0].observations)
    assert any("missing" in obs.lower() for obs in result.steps[0].observations)


def test_run_max_steps_branch() -> None:
    result = run_scenario(BRANCH_MAX_STEPS)
    assert result.stopped_reason == STOP_MAX_STEPS
    assert result.llm_calls == 2
    assert all(step.kind == "action" for step in result.steps)


def test_run_guarded_agent_rejects_empty_goal() -> None:
    with pytest.raises(ValueError):
        run_guarded_agent("  ", MockLLM([assistant_final("x")]))


def test_run_guarded_agent_rejects_bad_max_steps() -> None:
    with pytest.raises(ValueError):
        run_guarded_agent("goal", MockLLM([assistant_final("x")]), max_steps=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        run_guarded_agent("goal", MockLLM([assistant_final("x")]), max_steps=0)


def test_scenario_responses_unknown() -> None:
    with pytest.raises(ValueError, match="branch"):
        scenario_responses("not-a-branch")
    assert REQUIRED_BRANCHES == {
        BRANCH_FINAL,
        BRANCH_TOOL_OK,
        BRANCH_DENY,
        BRANCH_MAX_STEPS,
        BRANCH_BAD_ARGS,
    }


def test_render_coverage_report() -> None:
    report = render_coverage_report()
    for section in REQUIRED_REPORT_SECTIONS:
        assert f"## {section}" in report
    assert "Mock" in report or "mock" in report
    assert "Day 59" in report or "HITL" in report
