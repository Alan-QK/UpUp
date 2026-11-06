"""工具白名单 + 迷你 JSON Schema 校验。

本文件在练习中已给齐，今日勿改。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tools import ToolSpec

DECISION_ALLOW = "allow"
DECISION_DENY = "deny"

DANGEROUS_TOOL_NAMES = frozenset(
    {"shell_exec", "http_fetch_any", "read_secrets", "rm_rf"}
)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...]
    normalized_args: dict[str, Any] | None = None


@dataclass(frozen=True)
class GuardDecision:
    decision: str
    tool_name: str
    reason: str
    normalized_args: dict[str, Any] | None = None


def normalize_tool_name(name: str) -> str:
    normalized = name.strip().lower()
    if not normalized:
        raise ValueError("tool name must not be empty")
    return normalized


def _check_type(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    return True


def validate_args(spec: ToolSpec, args: dict[str, Any] | None) -> ValidationResult:
    """按 parameters.properties / required / additionalProperties 做迷你校验。"""
    schema = spec.parameters or {}
    props: dict[str, Any] = schema.get("properties") or {}
    required = list(schema.get("required") or [])
    allow_additional = schema.get("additionalProperties", True)
    raw = dict(args or {})

    errors: list[str] = []
    for key in required:
        if key not in raw:
            errors.append(f"missing required: {key}")

    if allow_additional is False:
        for key in raw:
            if key not in props:
                errors.append(f"unexpected property: {key}")

    normalized: dict[str, Any] = {}
    for key, value in raw.items():
        if key not in props:
            if allow_additional is False:
                continue
            normalized[key] = value
            continue
        expected = props[key].get("type")
        if expected and not _check_type(value, expected):
            errors.append(f"bad type for {key}: expected {expected}")
            continue
        if expected == "string" and isinstance(value, str):
            normalized[key] = value.strip()
        else:
            normalized[key] = value

    if errors:
        return ValidationResult(ok=False, errors=tuple(errors), normalized_args=None)
    return ValidationResult(ok=True, errors=(), normalized_args=normalized)


def authorize(
    tool_name: str,
    args: dict[str, Any] | None,
    catalog: dict[str, ToolSpec],
) -> GuardDecision:
    """白名单 + 危险名 + enabled + Schema。"""
    try:
        name = normalize_tool_name(tool_name)
    except ValueError:
        return GuardDecision(
            decision=DECISION_DENY,
            tool_name=str(tool_name),
            reason="invalid tool name",
        )

    if name in DANGEROUS_TOOL_NAMES:
        return GuardDecision(
            decision=DECISION_DENY,
            tool_name=name,
            reason="dangerous tool blocked",
        )

    spec = catalog.get(name)
    if spec is None:
        return GuardDecision(
            decision=DECISION_DENY,
            tool_name=name,
            reason="tool not in allowlist",
        )

    if not spec.enabled or spec.risk == "blocked":
        return GuardDecision(
            decision=DECISION_DENY,
            tool_name=name,
            reason="tool disabled or blocked",
        )

    result = validate_args(spec, args)
    if not result.ok:
        return GuardDecision(
            decision=DECISION_DENY,
            tool_name=name,
            reason="schema validation failed: " + "; ".join(result.errors),
        )

    return GuardDecision(
        decision=DECISION_ALLOW,
        tool_name=name,
        reason="ok",
        normalized_args=result.normalized_args or {},
    )
