"""HITL 确认钩子协议。

本文件在练习中已给齐，今日勿改。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from tools import ToolSpec

RISK_SAFE = "safe"
RISK_CONFIRM = "confirm"
RISK_BLOCKED = "blocked"
VALID_RISKS = frozenset({RISK_SAFE, RISK_CONFIRM, RISK_BLOCKED})

DECISION_APPROVE = "approve"
DECISION_REJECT = "reject"
DECISION_TIMEOUT = "timeout"
VALID_DECISIONS = frozenset(
    {DECISION_APPROVE, DECISION_REJECT, DECISION_TIMEOUT}
)


@dataclass(frozen=True)
class ConfirmationRequest:
    tool_name: str
    args: dict[str, Any]
    risk: str
    summary: str


@dataclass(frozen=True)
class ConfirmationDecision:
    decision: str
    note: str = ""


@dataclass(frozen=True)
class ConfirmationRecord:
    request: ConfirmationRequest
    decision: ConfirmationDecision


class ConfirmHook(Protocol):
    def __call__(self, request: ConfirmationRequest) -> ConfirmationDecision: ...


class ScriptedConfirmHook:
    """按序吐出预设决策；耗尽则 timeout。"""

    def __init__(self, decisions: list[ConfirmationDecision] | None = None) -> None:
        self._queue = list(decisions or [])

    def __call__(self, request: ConfirmationRequest) -> ConfirmationDecision:
        if not self._queue:
            return ConfirmationDecision(
                decision=DECISION_TIMEOUT,
                note="no more scripted decisions",
            )
        return self._queue.pop(0)


class AlwaysApprove:
    def __call__(self, request: ConfirmationRequest) -> ConfirmationDecision:
        return ConfirmationDecision(decision=DECISION_APPROVE, note="auto-approve")


def classify_risk(spec: ToolSpec | None, tool_name: str) -> str:
    if spec is None:
        return RISK_BLOCKED
    risk = spec.risk if spec.risk in VALID_RISKS else RISK_BLOCKED
    return risk


def build_confirmation_request(
    tool_name: str,
    args: dict[str, Any],
    risk: str,
) -> ConfirmationRequest:
    summary = f"准备执行 {tool_name}({', '.join(f'{k}={v!r}' for k, v in args.items())})"
    return ConfirmationRequest(
        tool_name=tool_name,
        args=dict(args),
        risk=risk,
        summary=summary,
    )
