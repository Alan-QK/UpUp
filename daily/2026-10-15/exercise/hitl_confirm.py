"""Day 59 练习：HITL 确认钩子。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——危险操作执行前暂停等人确认，不调用真实 LLM。
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Callable

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

STOP_FINAL = "final_answer"
STOP_MAX_STEPS = "max_steps"

BRANCH_SAFE_AUTO = "safe_auto"
BRANCH_APPROVE = "approve"
BRANCH_REJECT = "reject"
BRANCH_TIMEOUT = "timeout"
BRANCH_BLOCKED = "blocked"
REQUIRED_BRANCHES = frozenset(
    {
        BRANCH_SAFE_AUTO,
        BRANCH_APPROVE,
        BRANCH_REJECT,
        BRANCH_TIMEOUT,
        BRANCH_BLOCKED,
    }
)

REQUIRED_REPORT_SECTIONS = (
    "何为 HITL",
    "三档风险",
    "与 Guard 的分工",
    "关键分支",
    "明日预告",
)

ORDER_DB: dict[str, dict[str, str]] = {
    "ORD-1001": {
        "status": "shipped",
        "total": "128.00",
        "currency": "CNY",
        "city": "上海",
        "item": "机械键盘",
    },
    "ORD-2001": {
        "status": "paid",
        "total": "299.00",
        "currency": "CNY",
        "city": "北京",
        "item": "降噪耳机",
    },
}

DEFAULT_RISK_TABLE: dict[str, str] = {
    "order_lookup": RISK_SAFE,
    "get_time": RISK_SAFE,
    "refund_order": RISK_CONFIRM,
    "delete_account": RISK_CONFIRM,
    "shell_exec": RISK_BLOCKED,
    "rm_rf": RISK_BLOCKED,
    "read_secrets": RISK_BLOCKED,
}


@dataclass
class SideEffectLedger:
    """记录有副作用的执行结果，便于断言「拒绝后未执行」。"""

    refunds: list[str] = field(default_factory=list)
    deletions: list[str] = field(default_factory=list)

    def record_refund(self, order_id: str) -> None:
        # TODO
        raise NotImplementedError

    def record_deletion(self, account_id: str) -> None:
        # TODO
        raise NotImplementedError


@dataclass(frozen=True)
class ToolSpec:
    """工具规格。"""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]
    risk: str
    enabled: bool = True


@dataclass(frozen=True)
class ConfirmationRequest:
    """发给人的确认请求。"""

    tool_name: str
    args: dict[str, Any]
    reason: str
    risk: str


@dataclass(frozen=True)
class ConfirmationDecision:
    """人的确认决策。"""

    decision: str
    note: str = ""


@dataclass(frozen=True)
class ConfirmationRecord:
    """一次确认的完整轨迹。"""

    request: ConfirmationRequest
    decision: ConfirmationDecision


@dataclass(frozen=True)
class StepRecord:
    """Loop 中的一步。"""

    index: int
    kind: str  # "action" | "final"
    thought: str
    observations: tuple[str, ...]


@dataclass(frozen=True)
class AgentResult:
    """一次 Agent 运行结果。"""

    goal: str
    messages: list[dict[str, Any]]
    final_content: str
    stopped_reason: str
    steps: tuple[StepRecord, ...]
    llm_calls: int
    confirmations: tuple[ConfirmationRecord, ...]
    ledger: SideEffectLedger


@dataclass
class MockLLM:
    """按序吐出预设 assistant 消息；耗尽抛 RuntimeError（含 exhausted 或 no more）。"""

    _responses: list[dict[str, Any]] = field(default_factory=list)
    calls: list[list[dict[str, Any]]] = field(default_factory=list)

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        # TODO: 深拷贝 responses；初始化 calls=[]
        raise NotImplementedError

    def __call__(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        # TODO
        raise NotImplementedError

    @property
    def remaining(self) -> int:
        # TODO
        raise NotImplementedError


@dataclass
class ScriptedConfirmHook:
    """按序返回预设确认决策；耗尽时返回 timeout。

    构造参数可接受 ConfirmationDecision 或字符串 "approve"|"reject"|"timeout"。
    """

    _decisions: list[ConfirmationDecision] = field(default_factory=list)
    requests: list[ConfirmationRequest] = field(default_factory=list)

    def __init__(self, decisions: list[ConfirmationDecision | str]) -> None:
        # TODO
        raise NotImplementedError

    def __call__(self, request: ConfirmationRequest) -> ConfirmationDecision:
        # TODO: 记录 request；弹出下一条决策；空则 timeout
        raise NotImplementedError


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白压成单个空格。"""
    # TODO
    raise NotImplementedError


def normalize_tool_name(name: str) -> str:
    """strip + lower；空则 ValueError（消息含 name）。"""
    # TODO
    raise NotImplementedError


def classify_risk(
    tool_name: str,
    risk_table: dict[str, str] | None = None,
) -> str:
    """查风险表；未知工具视为 blocked。

    表内非法 risk → ValueError（消息含 risk / invalid）。
    """
    # TODO
    raise NotImplementedError


def order_lookup(order_id: str) -> str:
    """按订单号返回一行摘要；空 id → ValueError；未找到 → KeyError。"""
    # TODO
    raise NotImplementedError


def get_time(unit: str = "s") -> str:
    """教学用固定时间戳：s→1700000000，ms→1700000000000；其他 → ValueError。"""
    # TODO
    raise NotImplementedError


def make_refund_handler(ledger: SideEffectLedger) -> Callable[..., str]:
    """返回 refund_order(order_id)：成功则 ledger.record_refund 并返回含「已退款」的字符串。"""
    # TODO
    raise NotImplementedError


def make_delete_handler(ledger: SideEffectLedger) -> Callable[..., str]:
    """返回 delete_account(account_id)：成功则 ledger.record_deletion 并返回含「已删除」的字符串。"""
    # TODO
    raise NotImplementedError


def build_tool_catalog(ledger: SideEffectLedger) -> dict[str, ToolSpec]:
    """默认目录：order_lookup/get_time(safe) + refund_order/delete_account(confirm)。

    不得包含 shell_exec / rm_rf / read_secrets。
    """
    # TODO
    raise NotImplementedError


def validate_args(args: Any, schema: dict[str, Any]) -> tuple[bool, tuple[str, ...]]:
    """迷你 Schema 校验，返回 (ok, errors)。

    错误串需能匹配 missing / type / additional / enum / minLength（按需）。
    """
    # TODO
    raise NotImplementedError


def assistant_final(content: str) -> dict[str, Any]:
    """构造最终回答消息。"""
    # TODO
    raise NotImplementedError


def assistant_tool_call(
    call_id: str,
    name: str,
    arguments: dict[str, Any],
    content: str = "需要调用工具",
) -> dict[str, Any]:
    """构造带单条 tool_call 的 assistant 消息（arguments 需 json.dumps）。"""
    # TODO
    raise NotImplementedError


def has_tool_calls(assistant_message: dict[str, Any]) -> bool:
    """是否包含至少一条 tool_call。"""
    # TODO
    raise NotImplementedError


def parse_tool_calls(
    assistant_message: dict[str, Any],
) -> list[tuple[str, str, dict[str, Any]]]:
    """解析 tool_calls → [(call_id, tool_name, args_dict), ...]。"""
    # TODO
    raise NotImplementedError


def build_confirmation_reason(tool_name: str, args: dict[str, Any]) -> str:
    """生成给用户看的确认原因；退款/删号需提到对应 id。"""
    # TODO
    raise NotImplementedError


def hitl_execute(
    tool_name: str,
    args: dict[str, Any],
    *,
    catalog: dict[str, ToolSpec],
    confirm_hook: Callable[[ConfirmationRequest], ConfirmationDecision] | None,
    confirmations: list[ConfirmationRecord],
) -> str:
    """分级执行核心。

    - blocked（含未知工具名按 blocked）：返回 DENIED，且**不**调用钩子、不追加 confirmations
    - 不在 catalog / disabled / 参数非法：DENIED
    - safe：直接 handler
    - confirm：
      - 无钩子 → DENIED（消息含 hook / missing）
      - 调钩子，追加 ConfirmationRecord
      - reject → 观察含 rejected（建议前缀 REJECTED_BY_USER）
      - timeout → 观察含 timeout（建议前缀 CONFIRM_TIMEOUT）
      - approve → 执行 handler
    重要：拒绝/超时**不得**调用 handler（无副作用）。
    """
    # TODO
    raise NotImplementedError


def run_hitl_agent(
    goal: str,
    llm: MockLLM,
    *,
    confirm_hook: Callable[[ConfirmationRequest], ConfirmationDecision] | None = None,
    ledger: SideEffectLedger | None = None,
    max_steps: int = 6,
    system_prompt: str | None = None,
) -> AgentResult:
    """带 HITL 的最小 Agent Loop（结构类似 Day 58，执行改走 hitl_execute）。

    - 空 goal → ValueError
    - max_steps 必须是 int 且 >= 1（拒绝 bool）
    - 返回的 confirmations / ledger 供测试断言
    """
    # TODO
    raise NotImplementedError


def scenario_responses(branch: str) -> list[dict[str, Any]]:
    """返回关键分支的 Mock 响应。

    - safe_auto：order_lookup(ORD-1001) → 终答
    - approve / reject：refund_order(ORD-2001) → 终答
    - timeout：delete_account(ACC-9) → 终答
    - blocked：shell_exec → 终答
    - 未知 → ValueError（含 branch）
    """
    # TODO
    raise NotImplementedError


def run_scenario(branch: str) -> AgentResult:
    """用对应 ScriptedConfirmHook 跑一遍场景。

    - safe_auto：空决策列表的钩子（不应被调用）
    - approve / reject / timeout：单条对应决策
    - blocked：即使钩子是 approve，也不应产生 confirmations
    """
    # TODO
    raise NotImplementedError


def render_hitl_report(title: str = "Week 12 · HITL 确认钩子") -> str:
    """渲染 Markdown，必须包含 REQUIRED_REPORT_SECTIONS 全部二级标题。"""
    # TODO
    raise NotImplementedError
