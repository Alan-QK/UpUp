"""参考实现：请先自己完成 exercise/ 再对照。"""

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

# 工具名 → 风险档
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
        self.refunds.append(order_id)

    def record_deletion(self, account_id: str) -> None:
        self.deletions.append(account_id)


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
    """按序吐出预设 assistant 消息。"""

    _responses: list[dict[str, Any]] = field(default_factory=list)
    calls: list[list[dict[str, Any]]] = field(default_factory=list)

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self._responses = [copy.deepcopy(item) for item in responses]
        self.calls = []

    def __call__(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        self.calls.append(copy.deepcopy(messages))
        if not self._responses:
            raise RuntimeError("MockLLM exhausted: no more scripted responses")
        return copy.deepcopy(self._responses.pop(0))

    @property
    def remaining(self) -> int:
        return len(self._responses)


@dataclass
class ScriptedConfirmHook:
    """按序返回预设确认决策；耗尽时视为 timeout。"""

    _decisions: list[ConfirmationDecision] = field(default_factory=list)
    requests: list[ConfirmationRequest] = field(default_factory=list)

    def __init__(self, decisions: list[ConfirmationDecision | str]) -> None:
        parsed: list[ConfirmationDecision] = []
        for item in decisions:
            if isinstance(item, ConfirmationDecision):
                parsed.append(item)
            elif isinstance(item, str):
                key = item.strip().lower()
                if key not in VALID_DECISIONS:
                    raise ValueError(f"unknown decision: {item}")
                parsed.append(ConfirmationDecision(decision=key))
            else:
                raise TypeError("decision must be ConfirmationDecision or str")
        self._decisions = parsed
        self.requests = []

    def __call__(self, request: ConfirmationRequest) -> ConfirmationDecision:
        self.requests.append(request)
        if not self._decisions:
            return ConfirmationDecision(
                decision=DECISION_TIMEOUT,
                note="scripted hook exhausted",
            )
        return self._decisions.pop(0)


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def normalize_tool_name(name: str) -> str:
    normalized = name.strip().lower()
    if not normalized:
        raise ValueError("tool name must not be empty")
    return normalized


def classify_risk(
    tool_name: str,
    risk_table: dict[str, str] | None = None,
) -> str:
    """查风险表；未知工具视为 blocked（宁可拦）。"""
    table = risk_table if risk_table is not None else DEFAULT_RISK_TABLE
    normalized = normalize_tool_name(tool_name)
    risk = table.get(normalized, RISK_BLOCKED)
    if risk not in VALID_RISKS:
        raise ValueError(f"invalid risk level: {risk}")
    return risk


def order_lookup(order_id: str) -> str:
    cleaned = normalize_text(order_id)
    if not cleaned:
        raise ValueError("order_id must not be empty")
    if cleaned not in ORDER_DB:
        raise KeyError(f"order_id not found: {cleaned}")
    row = ORDER_DB[cleaned]
    return (
        f"订单 {cleaned}：status={row['status']}，合计 {row['total']} {row['currency']}，"
        f"收货地 {row['city']}，商品 {row['item']}"
    )


def get_time(unit: str = "s") -> str:
    normalized = unit.strip().lower()
    if normalized == "s":
        return "1700000000"
    if normalized == "ms":
        return "1700000000000"
    raise ValueError("unit must be s or ms")


def make_refund_handler(ledger: SideEffectLedger) -> Callable[..., str]:
    def refund_order(order_id: str) -> str:
        cleaned = normalize_text(order_id)
        if not cleaned:
            raise ValueError("order_id must not be empty")
        if cleaned not in ORDER_DB:
            raise KeyError(f"order_id not found: {cleaned}")
        ledger.record_refund(cleaned)
        row = ORDER_DB[cleaned]
        return f"已退款 {cleaned}，金额 {row['total']} {row['currency']}"

    return refund_order


def make_delete_handler(ledger: SideEffectLedger) -> Callable[..., str]:
    def delete_account(account_id: str) -> str:
        cleaned = normalize_text(account_id)
        if not cleaned:
            raise ValueError("account_id must not be empty")
        ledger.record_deletion(cleaned)
        return f"已删除账户 {cleaned}"

    return delete_account


def build_tool_catalog(ledger: SideEffectLedger) -> dict[str, ToolSpec]:
    """构建默认工具目录（含风险档）。"""
    refund = make_refund_handler(ledger)
    delete = make_delete_handler(ledger)
    specs = (
        ToolSpec(
            name="order_lookup",
            description="只读查询订单摘要",
            parameters={
                "type": "object",
                "properties": {"order_id": {"type": "string", "minLength": 1}},
                "required": ["order_id"],
                "additionalProperties": False,
            },
            handler=order_lookup,
            risk=RISK_SAFE,
        ),
        ToolSpec(
            name="get_time",
            description="教学用固定时间戳",
            parameters={
                "type": "object",
                "properties": {"unit": {"type": "string", "enum": ["s", "ms"]}},
                "required": [],
                "additionalProperties": False,
            },
            handler=get_time,
            risk=RISK_SAFE,
        ),
        ToolSpec(
            name="refund_order",
            description="对已支付订单发起退款（有副作用）",
            parameters={
                "type": "object",
                "properties": {"order_id": {"type": "string", "minLength": 1}},
                "required": ["order_id"],
                "additionalProperties": False,
            },
            handler=refund,
            risk=RISK_CONFIRM,
        ),
        ToolSpec(
            name="delete_account",
            description="删除用户账户（有副作用）",
            parameters={
                "type": "object",
                "properties": {"account_id": {"type": "string", "minLength": 1}},
                "required": ["account_id"],
                "additionalProperties": False,
            },
            handler=delete,
            risk=RISK_CONFIRM,
        ),
    )
    return {spec.name: spec for spec in specs}


def validate_args(args: Any, schema: dict[str, Any]) -> tuple[bool, tuple[str, ...]]:
    if not isinstance(args, dict):
        return False, ("args type must be object/dict",)

    errors: list[str] = []
    required = schema.get("required") or []
    properties: dict[str, Any] = schema.get("properties") or {}
    additional = schema.get("additionalProperties", False)

    for key in required:
        if key not in args:
            errors.append(f"missing required field: {key}")

    if additional is False:
        for key in args:
            if key not in properties:
                errors.append(f"additional property not allowed: {key}")

    for key, value in args.items():
        if key not in properties:
            continue
        prop = properties[key]
        expected_type = prop.get("type")
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"field {key} type must be string")
            continue
        if "minLength" in prop and isinstance(value, str):
            min_length = prop["minLength"]
            if len(value) < min_length:
                errors.append(f"field {key} minLength is {min_length}")
        if "enum" in prop and value not in prop["enum"]:
            errors.append(f"field {key} enum mismatch")

    return (not errors), tuple(errors)


def assistant_final(content: str) -> dict[str, Any]:
    return {"role": "assistant", "content": content}


def assistant_tool_call(
    call_id: str,
    name: str,
    arguments: dict[str, Any],
    content: str = "需要调用工具",
) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": content,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(arguments, ensure_ascii=False),
                },
            }
        ],
    }


def has_tool_calls(assistant_message: dict[str, Any]) -> bool:
    if not isinstance(assistant_message, dict):
        return False
    raw = assistant_message.get("tool_calls")
    return isinstance(raw, list) and len(raw) > 0


def parse_tool_calls(
    assistant_message: dict[str, Any],
) -> list[tuple[str, str, dict[str, Any]]]:
    raw = assistant_message.get("tool_calls")
    if not isinstance(raw, list):
        return []
    parsed: list[tuple[str, str, dict[str, Any]]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        call_id = str(item.get("id") or "")
        function = item.get("function") or {}
        if not isinstance(function, dict):
            continue
        name = str(function.get("name") or "")
        arguments = function.get("arguments")
        if isinstance(arguments, dict):
            args = dict(arguments)
        elif isinstance(arguments, str):
            try:
                loaded = json.loads(arguments)
            except json.JSONDecodeError:
                args = {}
            else:
                args = dict(loaded) if isinstance(loaded, dict) else {}
        else:
            args = {}
        parsed.append((call_id, name, args))
    return parsed


def build_confirmation_reason(tool_name: str, args: dict[str, Any]) -> str:
    """生成给用户看的确认原因摘要。"""
    normalized = normalize_tool_name(tool_name)
    if normalized == "refund_order":
        return f"即将退款订单 {args.get('order_id', '?')}，此操作不可自动撤销"
    if normalized == "delete_account":
        return f"即将删除账户 {args.get('account_id', '?')}，数据可能无法恢复"
    return f"即将执行高风险工具 {normalized}"


def hitl_execute(
    tool_name: str,
    args: dict[str, Any],
    *,
    catalog: dict[str, ToolSpec],
    confirm_hook: Callable[[ConfirmationRequest], ConfirmationDecision] | None,
    confirmations: list[ConfirmationRecord],
) -> str:
    """分级执行：blocked / safe / confirm(+钩子)。"""
    try:
        normalized = normalize_tool_name(tool_name)
    except ValueError as exc:
        return f"DENIED: invalid tool name ({exc})"

    risk = classify_risk(normalized)
    if risk == RISK_BLOCKED:
        return f"DENIED: tool is blocked and cannot be confirmed: {normalized}"

    spec = catalog.get(normalized)
    if spec is None:
        return f"DENIED: unknown tool not in catalog: {normalized}"
    if not spec.enabled:
        return f"DENIED: tool is disabled: {normalized}"

    ok, errors = validate_args(args, spec.parameters)
    if not ok:
        return f"DENIED: {'; '.join(errors)}"

    if risk == RISK_SAFE:
        try:
            return str(spec.handler(**args))
        except Exception as exc:  # noqa: BLE001
            return f"DENIED: handler error: {exc}"

    # RISK_CONFIRM
    if confirm_hook is None:
        return "DENIED: confirm hook missing for confirm-risk tool"

    request = ConfirmationRequest(
        tool_name=normalized,
        args=dict(args),
        reason=build_confirmation_reason(normalized, args),
        risk=risk,
    )
    decision = confirm_hook(request)
    if not isinstance(decision, ConfirmationDecision):
        return "DENIED: confirm hook returned invalid decision type"
    if decision.decision not in VALID_DECISIONS:
        return f"DENIED: invalid confirmation decision: {decision.decision}"

    confirmations.append(ConfirmationRecord(request=request, decision=decision))

    if decision.decision == DECISION_REJECT:
        return "REJECTED_BY_USER: human rejected the dangerous operation"
    if decision.decision == DECISION_TIMEOUT:
        return "CONFIRM_TIMEOUT: confirmation timed out; operation not executed"

    # approve
    try:
        return str(spec.handler(**args))
    except Exception as exc:  # noqa: BLE001
        return f"DENIED: handler error: {exc}"


def _default_system_prompt(catalog: dict[str, ToolSpec]) -> str:
    parts = []
    for name, spec in sorted(catalog.items()):
        parts.append(f"{name}({spec.risk})")
    return (
        "你是带 HITL 确认的助手。"
        f"工具与风险：{', '.join(parts)}。"
        "对 confirm 级工具，系统会在执行前征求用户确认。"
    )


def run_hitl_agent(
    goal: str,
    llm: MockLLM,
    *,
    confirm_hook: Callable[[ConfirmationRequest], ConfirmationDecision] | None = None,
    ledger: SideEffectLedger | None = None,
    max_steps: int = 6,
    system_prompt: str | None = None,
) -> AgentResult:
    if isinstance(max_steps, bool) or not isinstance(max_steps, int):
        raise ValueError("max_steps must be int")
    if max_steps < 1:
        raise ValueError("max_steps must be >= 1")

    cleaned_goal = normalize_text(goal)
    if not cleaned_goal:
        raise ValueError("goal must be non-empty")

    resolved_ledger = ledger if ledger is not None else SideEffectLedger()
    catalog = build_tool_catalog(resolved_ledger)
    system = (
        system_prompt
        if system_prompt is not None
        else _default_system_prompt(catalog)
    )

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": cleaned_goal},
    ]
    steps: list[StepRecord] = []
    confirmations: list[ConfirmationRecord] = []
    final_content = ""
    stopped_reason = STOP_MAX_STEPS
    llm_calls = 0

    for step_index in range(1, max_steps + 1):
        assistant = llm(messages)
        llm_calls += 1
        messages.append(copy.deepcopy(assistant))
        thought = normalize_text(str(assistant.get("content") or ""))

        if not has_tool_calls(assistant):
            final_content = str(assistant.get("content") or "")
            steps.append(
                StepRecord(
                    index=step_index,
                    kind="final",
                    thought=thought,
                    observations=(),
                )
            )
            stopped_reason = STOP_FINAL
            break

        observations: list[str] = []
        for call_id, name, args in parse_tool_calls(assistant):
            obs = hitl_execute(
                name,
                args,
                catalog=catalog,
                confirm_hook=confirm_hook,
                confirmations=confirmations,
            )
            observations.append(obs)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": name,
                    "content": obs,
                }
            )

        steps.append(
            StepRecord(
                index=step_index,
                kind="action",
                thought=thought,
                observations=tuple(observations),
            )
        )
        if step_index == max_steps:
            stopped_reason = STOP_MAX_STEPS
            final_content = observations[-1] if observations else thought
            break

    return AgentResult(
        goal=cleaned_goal,
        messages=messages,
        final_content=final_content,
        stopped_reason=stopped_reason,
        steps=tuple(steps),
        llm_calls=llm_calls,
        confirmations=tuple(confirmations),
        ledger=resolved_ledger,
    )


def scenario_responses(branch: str) -> list[dict[str, Any]]:
    key = branch.strip().lower()
    if key == BRANCH_SAFE_AUTO:
        return [
            assistant_tool_call(
                "c1",
                "order_lookup",
                {"order_id": "ORD-1001"},
                content="先查订单",
            ),
            assistant_final("订单 ORD-1001 已发货，收货地上海。"),
        ]
    if key == BRANCH_APPROVE:
        return [
            assistant_tool_call(
                "c2",
                "refund_order",
                {"order_id": "ORD-2001"},
                content="申请退款",
            ),
            assistant_final("退款已在人工确认后完成。"),
        ]
    if key == BRANCH_REJECT:
        return [
            assistant_tool_call(
                "c3",
                "refund_order",
                {"order_id": "ORD-2001"},
                content="申请退款",
            ),
            assistant_final("用户拒绝了退款，未执行。"),
        ]
    if key == BRANCH_TIMEOUT:
        return [
            assistant_tool_call(
                "c4",
                "delete_account",
                {"account_id": "ACC-9"},
                content="删除账户",
            ),
            assistant_final("确认超时，账户未删除。"),
        ]
    if key == BRANCH_BLOCKED:
        return [
            assistant_tool_call(
                "c5",
                "shell_exec",
                {"cmd": "rm -rf /"},
                content="试图执行危险命令",
            ),
            assistant_final("危险工具已被拦截，未询问用户。"),
        ]
    raise ValueError(f"unknown branch: {branch}")


def run_scenario(branch: str) -> AgentResult:
    key = branch.strip().lower()
    responses = scenario_responses(key)
    llm = MockLLM(responses)
    goals = {
        BRANCH_SAFE_AUTO: "查询订单 ORD-1001",
        BRANCH_APPROVE: "给订单 ORD-2001 退款",
        BRANCH_REJECT: "给订单 ORD-2001 退款",
        BRANCH_TIMEOUT: "删除账户 ACC-9",
        BRANCH_BLOCKED: "请执行 shell_exec",
    }
    if key not in goals:
        raise ValueError(f"unknown branch: {branch}")

    hook: ScriptedConfirmHook | None
    if key == BRANCH_SAFE_AUTO:
        hook = ScriptedConfirmHook([])  # 不应被调用
    elif key == BRANCH_APPROVE:
        hook = ScriptedConfirmHook([DECISION_APPROVE])
    elif key == BRANCH_REJECT:
        hook = ScriptedConfirmHook([DECISION_REJECT])
    elif key == BRANCH_TIMEOUT:
        hook = ScriptedConfirmHook([DECISION_TIMEOUT])
    else:
        hook = ScriptedConfirmHook([DECISION_APPROVE])  # blocked 不应问到

    return run_hitl_agent(goals[key], llm, confirm_hook=hook)


def render_hitl_report(title: str = "Week 12 · HITL 确认钩子") -> str:
    risk_lines = [
        "| 档位 | 含义 | 例子 |",
        "|------|------|------|",
        "| `safe` | 自动执行 | `order_lookup` / `get_time` |",
        "| `confirm` | 执行前问人 | `refund_order` / `delete_account` |",
        "| `blocked` | 永不执行、不问人 | `shell_exec` / `rm_rf` |",
    ]
    branch_lines = [
        "| 分支 | 行为 | 期望 |",
        "|------|------|------|",
        "| `safe_auto` | 只读写工具 | 无 confirmations；有订单摘要 |",
        "| `approve` | 退款 + 批准 | ledger 含 ORD-2001；观察含已退款 |",
        "| `reject` | 退款 + 拒绝 | ledger 空；观察含 rejected |",
        "| `timeout` | 删号 + 超时 | deletions 空；观察含 timeout |",
        "| `blocked` | shell_exec | confirmations 空；观察含 denied/blocked |",
    ]
    guard_lines = [
        "- Guard：白名单 + Schema，决定工具是否「合法出现」",
        "- HITL：合法但仍有副作用时，执行前征求人同意",
        "- blocked 比 confirm 更严：连确认入口都不给，避免误导",
    ]
    what_lines = [
        "- HITL = Human-in-the-Loop：危险动作执行前暂停等人确认",
        "- 钩子可注入：生产接 UI/工单，单测用 ScriptedConfirmHook",
        "- 前端删除确认 Modal ≈ Agent 的 confirm 节点",
    ]
    parts = [
        f"# {normalize_text(title)}",
        "",
        "## 何为 HITL",
        "",
        "\n".join(what_lines),
        "",
        "## 三档风险",
        "",
        "\n".join(risk_lines),
        "",
        "## 与 Guard 的分工",
        "",
        "\n".join(guard_lines),
        "",
        "## 关键分支",
        "",
        "\n".join(branch_lines),
        "",
        "## 明日预告",
        "",
        "- Day 60：里程碑 `tool-agent`——收拢 Schema / Loop / Guard / Mock / HITL",
        "- Phase 3 收官后进入 Phase 4：记忆 · 规划 · 多智能体",
        "",
    ]
    return "\n".join(parts)
