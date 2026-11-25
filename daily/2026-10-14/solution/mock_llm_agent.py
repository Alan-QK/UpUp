"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Callable

STOP_FINAL = "final_answer"
STOP_MAX_STEPS = "max_steps"
VALID_STOP_REASONS = frozenset({STOP_FINAL, STOP_MAX_STEPS})

BRANCH_FINAL = "final"
BRANCH_TOOL_OK = "tool_ok"
BRANCH_DENY = "deny"
BRANCH_MAX_STEPS = "max_steps"
BRANCH_BAD_ARGS = "bad_args"
REQUIRED_BRANCHES = frozenset(
    {
        BRANCH_FINAL,
        BRANCH_TOOL_OK,
        BRANCH_DENY,
        BRANCH_MAX_STEPS,
        BRANCH_BAD_ARGS,
    }
)

REQUIRED_REPORT_SECTIONS = (
    "为何 Mock",
    "关键分支",
    "断言建议",
    "与 Guard 的关系",
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
    "ORD-1002": {
        "status": "processing",
        "total": "59.90",
        "currency": "CNY",
        "city": "杭州",
        "item": "USB-C 数据线",
    },
}

DANGEROUS_TOOL_NAMES = frozenset(
    {"shell_exec", "http_fetch_any", "read_secrets", "rm_rf"}
)


@dataclass(frozen=True)
class ToolSpec:
    """允许列表中的一条工具规格。"""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]
    enabled: bool = True


@dataclass(frozen=True)
class StepRecord:
    """Loop 中的一步记录。"""

    index: int
    kind: str
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


@dataclass
class MockLLM:
    """按顺序吐出预设 assistant 消息；记录每次入参 messages 的深拷贝。"""

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


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def normalize_tool_name(name: str) -> str:
    normalized = name.strip().lower()
    if not normalized:
        raise ValueError("tool name must not be empty")
    return normalized


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


def build_default_allowlist() -> dict[str, ToolSpec]:
    order_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "minLength": 1},
        },
        "required": ["order_id"],
        "additionalProperties": False,
    }
    time_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "unit": {"type": "string", "enum": ["s", "ms"]},
        },
        "required": [],
        "additionalProperties": False,
    }
    specs = (
        ToolSpec(
            name="order_lookup",
            description="按订单号查询只读状态摘要",
            parameters=order_schema,
            handler=order_lookup,
            enabled=True,
        ),
        ToolSpec(
            name="get_time",
            description="返回教学用固定时间戳（s 或 ms）",
            parameters=time_schema,
            handler=get_time,
            enabled=True,
        ),
    )
    allowlist = {spec.name: spec for spec in specs}
    for dangerous in DANGEROUS_TOOL_NAMES:
        assert dangerous not in allowlist
    return allowlist


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


def guarded_execute(
    tool_name: str,
    args: dict[str, Any],
    allowlist: dict[str, ToolSpec] | None = None,
) -> str:
    resolved = allowlist if allowlist is not None else build_default_allowlist()
    try:
        normalized = normalize_tool_name(tool_name)
    except ValueError as exc:
        return f"DENIED: invalid tool name ({exc})"

    spec = resolved.get(normalized)
    if spec is None:
        return f"DENIED: unknown tool not in allowlist: {normalized}"
    if not spec.enabled:
        return f"DENIED: tool is disabled: {normalized}"

    ok, errors = validate_args(args, spec.parameters)
    if not ok:
        return f"DENIED: {'; '.join(errors)}"

    try:
        result = spec.handler(**args)
    except Exception as exc:  # noqa: BLE001 — 观察层吞业务异常
        return f"DENIED: handler error: {exc}"
    return str(result)


def _default_system_prompt(allowlist: dict[str, ToolSpec]) -> str:
    names = "、".join(sorted(allowlist.keys()))
    return (
        "你是带工具白名单的助手。"
        f"可用工具：{names}。"
        "需要订单信息时调用 order_lookup；信息足够后直接给出最终回答。"
    )


def run_guarded_agent(
    goal: str,
    llm: MockLLM,
    *,
    allowlist: dict[str, ToolSpec] | None = None,
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

    resolved = allowlist if allowlist is not None else build_default_allowlist()
    system = (
        system_prompt
        if system_prompt is not None
        else _default_system_prompt(resolved)
    )

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": cleaned_goal},
    ]
    steps: list[StepRecord] = []
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
            obs = guarded_execute(name, args, resolved)
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
    )


def scenario_responses(branch: str) -> list[dict[str, Any]]:
    key = branch.strip().lower()
    if key == BRANCH_FINAL:
        return [assistant_final("无需工具，直接说明 Mock 单测的价值。")]
    if key == BRANCH_TOOL_OK:
        return [
            assistant_tool_call(
                "c1",
                "order_lookup",
                {"order_id": "ORD-1001"},
                content="先查订单",
            ),
            assistant_final("订单 ORD-1001 已发货，收货地上海。"),
        ]
    if key == BRANCH_DENY:
        return [
            assistant_tool_call(
                "c2",
                "shell_exec",
                {"cmd": "rm -rf /"},
                content="试图执行危险命令",
            ),
            assistant_final("危险工具已被拒绝，我改用安全回答。"),
        ]
    if key == BRANCH_BAD_ARGS:
        return [
            assistant_tool_call(
                "c3",
                "order_lookup",
                {},
                content="漏传订单号",
            ),
            assistant_final("参数不合法，已停止查询。"),
        ]
    if key == BRANCH_MAX_STEPS:
        return [
            assistant_tool_call("c4", "get_time", {"unit": "s"}, content="第1次"),
            assistant_tool_call("c5", "get_time", {"unit": "ms"}, content="第2次"),
            assistant_tool_call("c6", "get_time", {"unit": "s"}, content="第3次"),
        ]
    raise ValueError(f"unknown branch: {branch}")


def run_scenario(
    branch: str,
    *,
    max_steps: int | None = None,
) -> AgentResult:
    key = branch.strip().lower()
    if max_steps is None:
        max_steps = 2 if key == BRANCH_MAX_STEPS else 6
    llm = MockLLM(scenario_responses(key))
    goals = {
        BRANCH_FINAL: "用一句话解释为何要 Mock LLM",
        BRANCH_TOOL_OK: "查询订单 ORD-1001 状态",
        BRANCH_DENY: "请执行 shell_exec 删除系统",
        BRANCH_BAD_ARGS: "查询订单但不要带 order_id",
        BRANCH_MAX_STEPS: "反复查询时间直到触顶",
    }
    if key not in goals:
        raise ValueError(f"unknown branch: {branch}")
    return run_guarded_agent(goals[key], llm, max_steps=max_steps)


def render_coverage_report(title: str = "Week 12 · Mock LLM 单测") -> str:
    branch_lines = [
        "| 分支 | 脚本要点 | 期望 stopped_reason |",
        "|------|----------|---------------------|",
        "| `final` | 首条即终答 | `final_answer` |",
        "| `tool_ok` | 合法 order_lookup → 终答 | `final_answer` |",
        "| `deny` | shell_exec → 终答 | `final_answer`（观察含 DENIED） |",
        "| `bad_args` | 缺 order_id → 终答 | `final_answer`（观察含 missing） |",
        "| `max_steps` | 连续工具调用触顶 | `max_steps` |",
    ]
    assert_lines = [
        "- 断言 `stopped_reason` 与 `llm_calls`，不要死磕模型措辞",
        "- 断言 tool observation 含 `ORD-1001` / `DENIED` / `missing`",
        "- 每个用例新建 `MockLLM`，避免共享可变状态",
        "- Mock 耗尽应抛 `RuntimeError`（含 exhausted / no more）",
    ]
    why_lines = [
        "- 真实 LLM 非确定、要密钥、要花钱，不适合当单元测试依赖",
        "- Mock 把「模型行为」变成可注入夹具，测的是 Loop / Guard / 消息拼接",
        "- 前端 mock fetch；Agent mock LLM——同一工程习惯",
    ]
    guard_lines = [
        "- Day 57：未知工具 / 坏参数在执行层 deny",
        "- Day 58：deny 写成 observation，Loop 可继续并被 pytest 钉死",
        "- 危险 handler 在 allowlist 外，单测证明「想调也调不到」",
    ]
    parts = [
        f"# {normalize_text(title)}",
        "",
        "## 为何 Mock",
        "",
        "\n".join(why_lines),
        "",
        "## 关键分支",
        "",
        "\n".join(branch_lines),
        "",
        "## 断言建议",
        "",
        "\n".join(assert_lines),
        "",
        "## 与 Guard 的关系",
        "",
        "\n".join(guard_lines),
        "",
        "## 明日预告",
        "",
        "- Day 59：HITL 确认钩子——危险操作执行前暂停，等待用户确认 / 拒绝",
        "- 随后：`tool-agent` 里程碑验收（Week 12 收官）",
        "",
    ]
    return "\n".join(parts)
