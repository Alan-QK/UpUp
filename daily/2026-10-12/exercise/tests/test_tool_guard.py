"""Day 57：工具白名单与参数校验测试。"""

from __future__ import annotations

import pytest

from tool_guard import (
    DANGEROUS_TOOL_NAMES,
    DECISION_ALLOW,
    DECISION_DENY,
    REQUIRED_REPORT_SECTIONS,
    ToolSpec,
    authorize_tool_call,
    build_default_allowlist,
    get_time,
    guarded_invoke,
    normalize_text,
    normalize_tool_name,
    order_lookup,
    render_guard_report,
    validate_args,
)


def test_normalize_helpers() -> None:
    assert normalize_tool_name(" Order_Lookup ") == "order_lookup"
    assert normalize_text("  a\n\nb  ") == "a b"
    with pytest.raises(ValueError, match="name"):
        normalize_tool_name("   ")


def test_order_lookup_and_get_time() -> None:
    text = order_lookup("ORD-1001")
    assert "ORD-1001" in text
    assert "shipped" in text
    assert "上海" in text
    with pytest.raises(ValueError):
        order_lookup("  ")
    with pytest.raises(KeyError):
        order_lookup("ORD-9999")

    assert get_time("s") == "1700000000"
    assert get_time("ms") == "1700000000000"
    assert get_time() == "1700000000"
    with pytest.raises(ValueError, match="unit"):
        get_time("hours")


def test_build_default_allowlist() -> None:
    allowlist = build_default_allowlist()
    assert set(allowlist.keys()) == {"order_lookup", "get_time"}
    for name in DANGEROUS_TOOL_NAMES:
        assert name not in allowlist

    order = allowlist["order_lookup"]
    assert isinstance(order, ToolSpec)
    assert order.enabled is True
    assert "order_id" in order.parameters.get("required", [])
    assert order.parameters.get("additionalProperties") is False

    clock = allowlist["get_time"]
    unit_schema = clock.parameters["properties"]["unit"]
    assert unit_schema.get("enum") == ["s", "ms"]


def test_validate_args_happy_and_errors() -> None:
    schema = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "minLength": 1},
            "unit": {"type": "string", "enum": ["s", "ms"]},
        },
        "required": ["order_id"],
        "additionalProperties": False,
    }
    ok = validate_args({"order_id": "ORD-1"}, schema)
    assert ok.ok is True
    assert ok.errors == ()

    not_dict = validate_args("oops", schema)
    assert not_dict.ok is False
    assert any("type" in e.lower() for e in not_dict.errors)

    missing = validate_args({}, schema)
    assert missing.ok is False
    assert any("missing" in e.lower() and "order_id" in e for e in missing.errors)

    extra = validate_args({"order_id": "ORD-1", "hack": 1}, schema)
    assert extra.ok is False
    assert any("additional" in e.lower() for e in extra.errors)

    bad_type = validate_args({"order_id": 123}, schema)
    assert bad_type.ok is False
    assert any("type" in e.lower() and "order_id" in e for e in bad_type.errors)

    short = validate_args({"order_id": ""}, schema)
    assert short.ok is False
    assert any("minlength" in e.lower() and "order_id" in e for e in short.errors)

    bad_enum = validate_args({"order_id": "ORD-1", "unit": "hours"}, schema)
    assert bad_enum.ok is False
    assert any("enum" in e.lower() and "unit" in e for e in bad_enum.errors)


def test_authorize_unknown_and_disabled() -> None:
    allow = authorize_tool_call("order_lookup", {"order_id": "ORD-1001"})
    assert allow.decision == DECISION_ALLOW
    assert "allow" in allow.reason.lower()
    assert allow.normalized_args == {"order_id": "ORD-1001"}

    unknown = authorize_tool_call("shell_exec", {"cmd": "ls"})
    assert unknown.decision == DECISION_DENY
    assert "unknown" in unknown.reason.lower() or "allowlist" in unknown.reason.lower()

    base = build_default_allowlist()
    disabled_spec = ToolSpec(
        name="order_lookup",
        description=base["order_lookup"].description,
        parameters=base["order_lookup"].parameters,
        handler=base["order_lookup"].handler,
        enabled=False,
    )
    disabled = authorize_tool_call(
        "order_lookup",
        {"order_id": "ORD-1001"},
        {"order_lookup": disabled_spec},
    )
    assert disabled.decision == DECISION_DENY
    assert "disabled" in disabled.reason.lower()


def test_authorize_schema_failure() -> None:
    decision = authorize_tool_call("order_lookup", {})
    assert decision.decision == DECISION_DENY
    assert "missing" in decision.reason.lower()


def test_guarded_invoke() -> None:
    result = guarded_invoke("order_lookup", {"order_id": "ORD-1001"})
    assert "ORD-1001" in result
    assert "shipped" in result

    assert guarded_invoke("get_time", {}) == "1700000000"
    assert guarded_invoke("get_time", {"unit": "ms"}) == "1700000000000"

    with pytest.raises(PermissionError) as exc:
        guarded_invoke("shell_exec", {"cmd": "rm -rf /"})
    assert "unknown" in str(exc.value).lower() or "allowlist" in str(exc.value).lower()

    with pytest.raises(PermissionError):
        guarded_invoke("order_lookup", {"order_id": 123})


def test_render_guard_report() -> None:
    report = render_guard_report()
    for section in REQUIRED_REPORT_SECTIONS:
        assert f"## {section}" in report
    assert "order_lookup" in report
    assert "get_time" in report
    assert "Day 58" in report or "Mock" in report or "单测" in report
