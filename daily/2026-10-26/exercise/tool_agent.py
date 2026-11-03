"""Day 60 练习：ToolAgent 编排层（Phase 3 里程碑核心）。

把 Week 9–12 的积木收成可演示作品：
Tool Schema → Guard → HITL → Agent Loop → Trace → Mock 验收。

请完成 TODO，使 tests/ 全部通过。
只用标准库 + pytest；不要引入 openai / langchain。

已给出、今日勿改：
  tools.py / guard.py / hitl.py / mock_llm.py / trace.py
"""

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
    RISK_SAFE,
    AlwaysApprove,
    ConfirmationDecision,
    ConfirmationRecord,
    ConfirmationRequest,
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
    openai_style_tools,
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
        """从沙箱目录构造 Agent。"""
        # TODO: 构造 Workspace + ToolAgent
        raise NotImplementedError

    def system_prompt(self) -> str:
        """生成 system 提示，列出可用工具名。"""
        # TODO
        raise NotImplementedError

    def run(self, goal: str, *, llm: ChatFn) -> AgentRunResult:
        """手写 Agent Loop：模型 →（可选）工具 → 观察回填，直到终答或触顶。

        规则要点：
        1. messages 以 system + user(goal) 开头
        2. 每轮调用 llm(messages)，计入 llm_calls
        3. 若无 tool_calls → kind=final，stopped_reason=final_answer
        4. 若有 tool_calls → 对每条：authorize → HITL（confirm）→ handler
           - deny / reject / timeout / blocked：写入 observation，不执行 handler
           - approve / safe：执行 handler，observation 为 JSON 文本
        5. 达到 max_steps 仍无终答 → stopped_reason=max_steps
        6. 每步写入 TraceStep；confirm 决策写入 confirmations
        """
        # TODO
        raise NotImplementedError

    def run_scenario(self, name: str) -> AgentRunResult:
        """内置演示场景（用 MockLLM，无需真模型）。

        支持：
        - calc_time：calculate → get_time → 终答
        - read_notes：list_files → read_file → 终答
        - http_docs：http_get → 终答
        - refund_approve：refund_order（批准）→ 终答
        - refund_reject：refund_order（拒绝）→ 终答
        - blocked_shell：试图 shell_exec → 被拒 → 终答
        - max_steps：反复 calculate 触顶
        """
        # TODO
        raise NotImplementedError

    def acceptance_checklist(self) -> dict[str, bool]:
        """对照 Phase 3 验收清单，返回布尔字典（键见 REQUIRED_ACCEPTANCE_KEYS）。"""
        # TODO
        raise NotImplementedError

    def render_acceptance_report(self) -> str:
        """渲染 Markdown 验收报告，必须包含 REQUIRED_REPORT_SECTIONS 全部二级标题。"""
        # TODO
        raise NotImplementedError

    def format_trace(self, result: AgentRunResult) -> str:
        """把运行结果格式化为 Markdown 轨迹。"""
        # TODO
        raise NotImplementedError


# ---- 以下辅助函数可在 TODO 中调用；也可自行实现 ----

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
    """返回 (llm, optional_hook_override)。hook 为 None 表示沿用 agent.confirm_hook。"""
    raise NotImplementedError  # TODO: 也可内联在 run_scenario 中实现
