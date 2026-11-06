"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from guard import DECISION_ALLOW, authorize
from hitl import (
    DECISION_APPROVE,
    DECISION_REJECT,
    DECISION_TIMEOUT,
    RISK_BLOCKED,
    RISK_CONFIRM,
    AlwaysApprove,
    ConfirmationDecision,
    ConfirmationRecord,
    ConfirmHook,
    ScriptedConfirmHook,
    build_confirmation_request,
    classify_risk,
)
from mock_llm import MockLLM, assistant_text, assistant_tool_call, parse_tool_arguments
from tools import (
    SideEffectLedger,
    ToolSpec,
    Workspace,
    build_default_tools,
)
from trace import TraceStep, extract_tool_names, format_trace_markdown

STOP_FINAL = "final_answer"
STOP_MAX_STEPS = "max_steps"
VALID_STOP_REASONS = frozenset({STOP_FINAL, STOP_MAX_STEPS})

ChatFn = Callable[[list[dict[str, Any]]], dict[str, Any]]

REQUIRED_ACCEPTANCE_KEYS = (
    "tools_ge_3",
    "loop_runs",
    "max_steps",
    "trace",
    "security",
    "mock_tests",
)

REQUIRED_REPORT_SECTIONS = (
    "能力清单",
    "架构示意",
    "安全边界",
    "验收结果",
    "坏轨迹复盘",
    "下一阶段",
)


class ToolAgentError(ValueError):
    """tool-agent 参数或状态不合法。"""


@dataclass(frozen=True)
class AgentRunResult:
    """一次 Agent 运行结果。"""

    goal: str
    final_content: str
    stopped_reason: str
    steps: tuple[TraceStep, ...]
    confirmations: tuple[ConfirmationRecord, ...]
    llm_calls: int
    messages: tuple[dict[str, Any], ...]
    refunded_orders: frozenset[str]


@dataclass
class ToolAgent:
    """最小可演示 Tool Agent：Guard + HITL + Loop + Trace。"""

    workspace: Workspace
    ledger: SideEffectLedger = field(default_factory=SideEffectLedger)
    max_steps: int = 6
    confirm_hook: ConfirmHook | None = None
    catalog: dict[str, ToolSpec] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.max_steps, bool) or not isinstance(self.max_steps, int):
            raise ToolAgentError("max_steps must be int")
        if self.max_steps < 1:
            raise ToolAgentError("max_steps must be >= 1")
        if not self.catalog:
            self.catalog = build_default_tools(self.workspace, self.ledger)
        if self.confirm_hook is None:
            self.confirm_hook = AlwaysApprove()

    @classmethod
    def from_workspace(
        cls,
        root: Path | str,
        *,
        max_steps: int = 6,
        confirm_hook: ConfirmHook | None = None,
    ) -> ToolAgent:
        ws = Workspace(Path(root))
        return cls(workspace=ws, max_steps=max_steps, confirm_hook=confirm_hook)

    def system_prompt(self) -> str:
        names = [
            name
            for name, spec in self.catalog.items()
            if spec.enabled and spec.risk != "blocked"
        ]
        joined = "、".join(sorted(names))
        return (
            "你是带工具调用的助手，遵循 Thought → Action → Observation。"
            f"可用工具：{joined}。"
            "需要外部事实或计算时先调用工具；信息足够后直接给出最终回答。"
            "禁止执行任意 shell；退款等有副作用操作需等待确认。"
        )

    def run(self, goal: str, *, llm: ChatFn) -> AgentRunResult:
        text = goal.strip() if isinstance(goal, str) else ""
        if not text:
            raise ToolAgentError("goal must not be empty")

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": text},
        ]
        steps: list[TraceStep] = []
        confirmations: list[ConfirmationRecord] = []
        llm_calls = 0
        final_content = ""
        stopped_reason = STOP_MAX_STEPS

        for step_index in range(1, self.max_steps + 1):
            assistant = llm(messages)
            llm_calls += 1
            if not isinstance(assistant, dict):
                raise ToolAgentError("llm must return a dict message")

            messages.append(assistant)
            thought = _normalize_text(str(assistant.get("content") or ""))

            if not _has_tool_calls(assistant):
                final_content = thought
                steps.append(
                    TraceStep(
                        index=step_index,
                        kind="final",
                        thought=thought,
                        tool_names=(),
                        observations=(),
                    )
                )
                stopped_reason = STOP_FINAL
                break

            tool_names = extract_tool_names(assistant)
            observations: list[str] = []
            raw_calls = assistant.get("tool_calls") or []
            for call in raw_calls:
                obs, conf = self._execute_one_call(call)
                observations.append(obs)
                if conf is not None:
                    confirmations.append(conf)
                call_id = ""
                if isinstance(call, dict):
                    call_id = str(call.get("id") or "")
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": obs,
                    }
                )

            steps.append(
                TraceStep(
                    index=step_index,
                    kind="action",
                    thought=thought,
                    tool_names=tool_names,
                    observations=tuple(observations),
                )
            )
        else:
            # 循环正常耗尽（未 break）
            if steps and steps[-1].kind == "action":
                final_content = (
                    _normalize_text(steps[-1].thought)
                    or f"stopped at max_steps={self.max_steps}"
                )
            stopped_reason = STOP_MAX_STEPS

        return AgentRunResult(
            goal=text,
            final_content=final_content,
            stopped_reason=stopped_reason,
            steps=tuple(steps),
            confirmations=tuple(confirmations),
            llm_calls=llm_calls,
            messages=tuple(messages),
            refunded_orders=frozenset(self.ledger.refunded_orders),
        )

    def _execute_one_call(
        self,
        call: Any,
    ) -> tuple[str, ConfirmationRecord | None]:
        if not isinstance(call, dict):
            return (
                _observation_payload(
                    ok=False,
                    tool_name="?",
                    content="invalid tool_call",
                    status="denied",
                ),
                None,
            )

        fn = call.get("function") if isinstance(call.get("function"), dict) else {}
        tool_name = str(fn.get("name") or "")
        try:
            args = parse_tool_arguments(fn.get("arguments"))
        except (ValueError, json.JSONDecodeError) as exc:
            return (
                _observation_payload(
                    ok=False,
                    tool_name=tool_name or "?",
                    content=str(exc),
                    status="bad_args",
                ),
                None,
            )

        decision = authorize(tool_name, args, self.catalog)
        if decision.decision != DECISION_ALLOW:
            return (
                _observation_payload(
                    ok=False,
                    tool_name=decision.tool_name,
                    content=decision.reason,
                    status="denied",
                ),
                None,
            )

        name = decision.tool_name
        norm_args = decision.normalized_args or {}
        spec = self.catalog[name]
        risk = classify_risk(spec, name)

        if risk == RISK_BLOCKED:
            return (
                _observation_payload(
                    ok=False,
                    tool_name=name,
                    content="blocked",
                    status="denied",
                ),
                None,
            )

        conf_record: ConfirmationRecord | None = None
        if risk == RISK_CONFIRM:
            request = build_confirmation_request(name, norm_args, risk)
            hook = self.confirm_hook or AlwaysApprove()
            conf_decision = hook(request)
            if conf_decision.decision not in {
                DECISION_APPROVE,
                DECISION_REJECT,
                DECISION_TIMEOUT,
            }:
                conf_decision = ConfirmationDecision(
                    decision=DECISION_TIMEOUT,
                    note="invalid decision",
                )
            conf_record = ConfirmationRecord(request=request, decision=conf_decision)
            if conf_decision.decision == DECISION_REJECT:
                return (
                    _observation_payload(
                        ok=False,
                        tool_name=name,
                        content="REJECTED_BY_USER",
                        status="rejected",
                    ),
                    conf_record,
                )
            if conf_decision.decision == DECISION_TIMEOUT:
                return (
                    _observation_payload(
                        ok=False,
                        tool_name=name,
                        content="CONFIRM_TIMEOUT",
                        status="timeout",
                    ),
                    conf_record,
                )

        try:
            result = spec.handler(**norm_args)
        except Exception as exc:  # noqa: BLE001 — 工具错误回传观察
            return (
                _observation_payload(
                    ok=False,
                    tool_name=name,
                    content=str(exc),
                    status="error",
                ),
                conf_record,
            )

        return (
            _observation_payload(
                ok=True,
                tool_name=name,
                content=result,
                status="ok",
            ),
            conf_record,
        )

    def run_scenario(self, name: str) -> AgentRunResult:
        key = name.strip().lower()
        llm, hook = _scenario_pack(key, self)
        if hook is not None:
            self.confirm_hook = hook
        # 场景开始前清空副作用，避免互相污染
        self.ledger.refunded_orders.clear()
        self.ledger.deleted_accounts.clear()
        goals = {
            "calc_time": "先算 12*(3+4)，再告诉我当前 UTC 时间。",
            "read_notes": "列出工作区文件并阅读 notes.txt 摘要。",
            "http_docs": "抓取 https://docs.python.org 的摘要。",
            "refund_approve": "查询 ORD-1001 并退款。",
            "refund_reject": "查询 ORD-1001 并退款。",
            "blocked_shell": "用 shell 删除所有文件。",
            "max_steps": "反复计算 1+1。",
        }
        if key not in goals:
            raise ToolAgentError(f"unknown scenario: {name}")
        return self.run(goals[key], llm=llm)

    def acceptance_checklist(self) -> dict[str, bool]:
        enabled = [
            s
            for s in self.catalog.values()
            if s.enabled and s.risk != "blocked"
        ]
        tools_ge_3 = len(enabled) >= 3

        # 轻量自检：跑一个短场景证明 loop / trace / max_steps / security
        demo = self.from_workspace(
            self.workspace.root,
            max_steps=self.max_steps,
            confirm_hook=AlwaysApprove(),
        )
        calc = demo.run_scenario("calc_time")
        loop_runs = calc.stopped_reason == STOP_FINAL and calc.llm_calls >= 2
        trace_ok = len(calc.steps) >= 1 and bool(
            format_trace_markdown(
                calc.goal, calc.steps, final=calc.final_content, reason=calc.stopped_reason
            )
        )

        capped = ToolAgent.from_workspace(
            self.workspace.root, max_steps=2, confirm_hook=AlwaysApprove()
        )
        capped_result = capped.run_scenario("max_steps")
        max_steps_ok = capped_result.stopped_reason == STOP_MAX_STEPS

        blocked = ToolAgent.from_workspace(
            self.workspace.root, max_steps=4, confirm_hook=AlwaysApprove()
        )
        blocked_result = blocked.run_scenario("blocked_shell")
        security_ok = (
            blocked_result.stopped_reason == STOP_FINAL
            and any("denied" in obs for step in blocked_result.steps for obs in step.observations)
        )

        # mock_tests：本方法本身即可被 pytest 调用；此处标记为 True 表示场景可跑
        mock_tests = tools_ge_3 and loop_runs and max_steps_ok and security_ok and trace_ok

        return {
            "tools_ge_3": tools_ge_3,
            "loop_runs": loop_runs,
            "max_steps": max_steps_ok,
            "trace": trace_ok,
            "security": security_ok,
            "mock_tests": mock_tests,
        }

    def render_acceptance_report(self) -> str:
        checklist = self.acceptance_checklist()
        enabled = sorted(
            s.name
            for s in self.catalog.values()
            if s.enabled and s.risk != "blocked"
        )
        lines = [
            "# tool-agent 验收报告",
            "",
            "## 能力清单",
            "",
            f"- 启用工具：{', '.join(enabled)}",
            f"- max_steps：{self.max_steps}",
            "- 能力：手写 Loop、Guard 白名单、HITL 确认、Trace 回放、MockLLM 场景",
            "",
            "## 架构示意",
            "",
            "```text",
            "goal → MockLLM/Chat",
            "     → authorize(Guard)",
            "     → HITL(confirm?)",
            "     → handler → observation → loop",
            "     → TraceStep[]",
            "```",
            "",
            "## 安全边界",
            "",
            "- 危险名 / blocked 工具永不执行",
            "- 沙箱只读文件，禁止 `..` 越界",
            "- http_get 仅 https + host 白名单（假响应，无真网）",
            "- refund_order 必须经 HITL",
            "",
            "## 验收结果",
            "",
        ]
        for key in REQUIRED_ACCEPTANCE_KEYS:
            flag = "PASS" if checklist.get(key) else "FAIL"
            lines.append(f"- {key}: {flag}")
        lines.extend(
            [
                "",
                "## 坏轨迹复盘",
                "",
                "> 请填写一次异常轨迹：误退款 / 越权工具 / 触顶无终答，并写改进。",
                "",
                "1. 现象：",
                "2. 原因：",
                "3. 改进：",
                "",
                "## 下一阶段",
                "",
                "进入 Phase 4：会话记忆 / 摘要记忆 / 长期向量记忆与多智能体协作。",
                "",
            ]
        )
        return "\n".join(lines)

    def format_trace(self, result: AgentRunResult) -> str:
        return format_trace_markdown(
            result.goal,
            result.steps,
            final=result.final_content,
            reason=result.stopped_reason,
        )


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _has_tool_calls(assistant: dict[str, Any]) -> bool:
    raw = assistant.get("tool_calls")
    return isinstance(raw, list) and len(raw) > 0


def _observation_payload(
    *,
    ok: bool,
    tool_name: str,
    content: Any,
    status: str,
) -> str:
    return json.dumps(
        {"ok": ok, "tool": tool_name, "status": status, "content": content},
        ensure_ascii=False,
        default=str,
    )


def _scenario_pack(
    name: str,
    agent: ToolAgent,
) -> tuple[MockLLM, ConfirmHook | None]:
    if name == "calc_time":
        llm = MockLLM(
            [
                assistant_tool_call(
                    "calculate",
                    {"expression": "12*(3+4)"},
                    call_id="c1",
                    thought="先算表达式",
                ),
                assistant_tool_call(
                    "get_time",
                    {},
                    call_id="c2",
                    thought="再取时间",
                ),
                assistant_text("计算结果是 84，时间已取回。"),
            ]
        )
        return llm, None

    if name == "read_notes":
        llm = MockLLM(
            [
                assistant_tool_call(
                    "list_files",
                    {"relative_dir": "."},
                    call_id="c1",
                    thought="先看目录",
                ),
                assistant_tool_call(
                    "read_file",
                    {"relative_path": "notes.txt"},
                    call_id="c2",
                    thought="读 notes",
                ),
                assistant_text("已阅读 notes.txt。"),
            ]
        )
        return llm, None

    if name == "http_docs":
        llm = MockLLM(
            [
                assistant_tool_call(
                    "http_get",
                    {"url": "https://docs.python.org"},
                    call_id="c1",
                    thought="抓文档",
                ),
                assistant_text("已获取 Python 文档摘要。"),
            ]
        )
        return llm, None

    if name == "refund_approve":
        llm = MockLLM(
            [
                assistant_tool_call(
                    "order_lookup",
                    {"order_id": "ORD-1001"},
                    call_id="c1",
                    thought="先查单",
                ),
                assistant_tool_call(
                    "refund_order",
                    {"order_id": "ORD-1001"},
                    call_id="c2",
                    thought="再退款",
                ),
                assistant_text("ORD-1001 已退款。"),
            ]
        )
        hook = ScriptedConfirmHook(
            [ConfirmationDecision(decision=DECISION_APPROVE, note="ok")]
        )
        return llm, hook

    if name == "refund_reject":
        llm = MockLLM(
            [
                assistant_tool_call(
                    "order_lookup",
                    {"order_id": "ORD-1001"},
                    call_id="c1",
                    thought="先查单",
                ),
                assistant_tool_call(
                    "refund_order",
                    {"order_id": "ORD-1001"},
                    call_id="c2",
                    thought="再退款",
                ),
                assistant_text("用户拒绝退款，未执行。"),
            ]
        )
        hook = ScriptedConfirmHook(
            [ConfirmationDecision(decision=DECISION_REJECT, note="no")]
        )
        return llm, hook

    if name == "blocked_shell":
        llm = MockLLM(
            [
                assistant_tool_call(
                    "shell_exec",
                    {"cmd": "rm -rf /"},
                    call_id="c1",
                    thought="危险操作",
                ),
                assistant_text("无法执行危险 shell。"),
            ]
        )
        return llm, None

    if name == "max_steps":
        llm = MockLLM(
            [
                assistant_tool_call(
                    "calculate",
                    {"expression": "1+1"},
                    call_id=f"c{i}",
                    thought="继续算",
                )
                for i in range(1, 8)
            ]
        )
        return llm, AlwaysApprove()

    raise ToolAgentError(f"unknown scenario: {name}")
