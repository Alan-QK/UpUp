"""Day 58 练习：Mock LLM 单测。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——今天用假模型钉死 Agent 关键分支，不调用真实 LLM。
"""

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

# 模拟订单库（只读）
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


@dataclass
class MockLLM:
    """按顺序吐出预设 assistant 消息；记录每次入参 messages 的深拷贝。

    - responses 耗尽时：抛 RuntimeError，消息必须包含 exhausted 或 no more
    - 每次 __call__：先把 messages 深拷贝追加到 calls，再弹出下一条响应
    """

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
        """还剩多少条未消费响应。"""
        # TODO
        raise NotImplementedError


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白压成单个空格。"""
    # TODO
    raise NotImplementedError


def normalize_tool_name(name: str) -> str:
    """strip + lower；空则 ValueError（消息含 name）。"""
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


def build_default_allowlist() -> dict[str, ToolSpec]:
    """默认允许列表：仅 order_lookup + get_time（同 Day 57 约定）。

    - order_lookup：required=["order_id"]；order_id string minLength=1；
      additionalProperties=false
    - get_time：unit enum ["s","ms"]；required=[]；additionalProperties=false
    - 不得包含 DANGEROUS_TOOL_NAMES
    """
    # TODO
    raise NotImplementedError


def validate_args(args: Any, schema: dict[str, Any]) -> tuple[bool, tuple[str, ...]]:
    """迷你 Schema 校验，返回 (ok, errors)。

    规则同 Day 57（可简化实现，但错误串需含 missing/type/additional/enum/minLength）。
    """
    # TODO
    raise NotImplementedError


def assistant_final(content: str) -> dict[str, Any]:
    """构造最终回答消息：{"role":"assistant","content":...}，无 tool_calls。"""
    # TODO
    raise NotImplementedError


def assistant_tool_call(
    call_id: str,
    name: str,
    arguments: dict[str, Any],
    content: str = "需要调用工具",
) -> dict[str, Any]:
    """构造带单条 tool_call 的 assistant 消息（OpenAI 风格）。

    arguments 需 json.dumps 进 function.arguments 字符串。
    """
    # TODO
    raise NotImplementedError


def has_tool_calls(assistant_message: dict[str, Any]) -> bool:
    """是否包含至少一条 tool_call。"""
    # TODO
    raise NotImplementedError


def parse_tool_calls(
    assistant_message: dict[str, Any],
) -> list[tuple[str, str, dict[str, Any]]]:
    """解析 tool_calls → [(call_id, tool_name, args_dict), ...]。

    - arguments 为 str → json.loads，必须是 object
    - arguments 已是 dict → 浅拷贝
    - 非法 → 该条跳过或按空 dict（实现任选，但测试用合法输入）
    """
    # TODO
    raise NotImplementedError


def guarded_execute(
    tool_name: str,
    args: dict[str, Any],
    allowlist: dict[str, ToolSpec] | None = None,
) -> str:
    """先授权再执行；失败时返回以 DENIED: 开头的说明字符串（不抛 PermissionError）。

    成功：返回 handler 结果的 str。
    拒绝原因应可读，并包含 denied（大小写不限亦可在返回里固定 DENIED: 前缀）。
    """
    # TODO
    raise NotImplementedError


def run_guarded_agent(
    goal: str,
    llm: MockLLM,
    *,
    allowlist: dict[str, ToolSpec] | None = None,
    max_steps: int = 6,
    system_prompt: str | None = None,
) -> AgentResult:
    """最小带 Guard 的 Agent Loop。

    流程：
    1. normalize goal；空 → ValueError
    2. max_steps 必须是 int 且 >= 1（拒绝 bool）
    3. messages = [system, user]
    4. 循环最多 max_steps 次模型调用：
       - 调 llm(messages)
       - 追加 assistant
       - 若无 tool_calls → 记 final step，stopped_reason=final_answer，结束
       - 若有 tool_calls → 对每个调用 guarded_execute，追加 role=tool 消息；
         记 action step；若已达 max_steps 次调用仍未 final → stopped_reason=max_steps
    5. 返回 AgentResult（llm_calls = 实际模型调用次数）
    """
    # TODO
    raise NotImplementedError


def scenario_responses(branch: str) -> list[dict[str, Any]]:
    """返回某关键分支的预设 Mock 响应列表。

    - final：一条终答
    - tool_ok：order_lookup(ORD-1001) → 终答
    - deny：shell_exec → 终答（观察会 DENIED）
    - bad_args：order_lookup 缺 order_id → 终答
    - max_steps：至少 3 条连续工具调用（配合 max_steps=2 测触顶）
    - 未知 branch → ValueError，消息含 branch
    """
    # TODO
    raise NotImplementedError


def run_scenario(
    branch: str,
    *,
    max_steps: int | None = None,
) -> AgentResult:
    """用 scenario_responses + MockLLM 跑一遍。

    max_steps 缺省：max_steps 分支用 2，其余用 6。
    """
    # TODO
    raise NotImplementedError


def render_coverage_report(title: str = "Week 12 · Mock LLM 单测") -> str:
    """渲染 Markdown 覆盖说明，必须包含 REQUIRED_REPORT_SECTIONS 全部二级标题。"""
    # TODO
    raise NotImplementedError
