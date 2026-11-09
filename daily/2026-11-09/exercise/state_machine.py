"""Day 69 练习：Agent 状态机（Plan / Execute / Reflect / HITL）。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——不调用 LLM。

提示：
- 状态 / 事件常量、Transition、HITL_RESUME_DEFAULT 已给齐
- 先写 default_transitions / build_transition_map / can_transition
- 再实现 AgentStateMachine.send（含 hitl_approved 动态恢复）
- 然后 simulate_* / render_mermaid / report
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

# --- 状态 ---

STATE_IDLE = "idle"
STATE_PLANNING = "planning"
STATE_EXECUTING = "executing"
STATE_REFLECTING = "reflecting"
STATE_AWAITING_HITL = "awaiting_hitl"
STATE_DONE = "done"
STATE_ABORTED = "aborted"

VALID_STATES = frozenset(
    {
        STATE_IDLE,
        STATE_PLANNING,
        STATE_EXECUTING,
        STATE_REFLECTING,
        STATE_AWAITING_HITL,
        STATE_DONE,
        STATE_ABORTED,
    }
)

TERMINAL_STATES = frozenset({STATE_DONE, STATE_ABORTED})

# --- 事件 ---

EVENT_GOAL_RECEIVED = "goal_received"
EVENT_PLAN_READY = "plan_ready"
EVENT_EXECUTION_FINISHED = "execution_finished"
EVENT_DECISION_ACCEPT = "decision_accept"
EVENT_DECISION_RETRY = "decision_retry"
EVENT_DECISION_REVISE = "decision_revise"
EVENT_DECISION_ABORT = "decision_abort"
EVENT_NEED_HITL = "need_hitl"
EVENT_HITL_APPROVED = "hitl_approved"
EVENT_HITL_REJECTED = "hitl_rejected"
EVENT_RESET = "reset"

VALID_EVENTS = frozenset(
    {
        EVENT_GOAL_RECEIVED,
        EVENT_PLAN_READY,
        EVENT_EXECUTION_FINISHED,
        EVENT_DECISION_ACCEPT,
        EVENT_DECISION_RETRY,
        EVENT_DECISION_REVISE,
        EVENT_DECISION_ABORT,
        EVENT_NEED_HITL,
        EVENT_HITL_APPROVED,
        EVENT_HITL_REJECTED,
        EVENT_RESET,
    }
)

# Day 68 决策 → 事件
DECISION_TO_EVENT: dict[str, str] = {
    "accept": EVENT_DECISION_ACCEPT,
    "retry": EVENT_DECISION_RETRY,
    "revise": EVENT_DECISION_REVISE,
    "abort": EVENT_DECISION_ABORT,
}

# need_hitl 时：各源状态批准后应恢复到哪里
HITL_RESUME_DEFAULT: dict[str, str] = {
    STATE_PLANNING: STATE_EXECUTING,
    STATE_EXECUTING: STATE_REFLECTING,
    STATE_REFLECTING: STATE_DONE,
}

REQUIRED_REPORT_SECTIONS = (
    "何为 Agent 状态机",
    "核心状态与主路径",
    "今日演示统计",
    "Mermaid 状态图",
    "明日预告",
)


@dataclass(frozen=True)
class Transition:
    """一条转移：source + event → target。"""

    source: str
    event: str
    target: str
    note: str = ""

    def __post_init__(self) -> None:
        if self.source not in VALID_STATES:
            raise ValueError(f"invalid source: {self.source}")
        if self.target not in VALID_STATES:
            raise ValueError(f"invalid target: {self.target}")
        if self.event not in VALID_EVENTS:
            raise ValueError(f"invalid event: {self.event}")
        if not isinstance(self.note, str):
            raise TypeError("note must be str")


@dataclass(frozen=True)
class TransitionRecord:
    """一次实际发生的跳转记录。"""

    from_state: str
    event: str
    to_state: str
    note: str = ""

    def __post_init__(self) -> None:
        if self.from_state not in VALID_STATES:
            raise ValueError(f"invalid from_state: {self.from_state}")
        if self.to_state not in VALID_STATES:
            raise ValueError(f"invalid to_state: {self.to_state}")
        if self.event not in VALID_EVENTS:
            raise ValueError(f"invalid event: {self.event}")


class IllegalTransitionError(ValueError):
    """非法状态转移。"""


def default_transitions() -> tuple[Transition, ...]:
    """今日默认 Agent 生命周期转移表。

    必须覆盖主路径、纠错环、HITL 进入/拒绝、终态 reset。
    注意：hitl_approved 目标由运行时 hitl_resume 决定，不要写进静态表。
    """
    # TODO
    raise NotImplementedError


def build_transition_map(
    transitions: Sequence[Transition] | None = None,
) -> dict[tuple[str, str], Transition]:
    """(source, event) → Transition；重复键抛错。"""
    # TODO: transitions is None 时用 default_transitions()
    raise NotImplementedError


def list_events_from(state: str, transitions: Sequence[Transition] | None = None) -> list[str]:
    """列出某状态下合法事件（排序后；含 hitl_approved 动态边）。"""
    # TODO
    raise NotImplementedError


def can_transition(
    state: str,
    event: str,
    transitions: Sequence[Transition] | None = None,
) -> bool:
    """是否存在 (state, event) 转移（含 hitl_approved 动态边）。"""
    # TODO
    raise NotImplementedError


def lookup_transition(
    state: str,
    event: str,
    transitions: Sequence[Transition] | None = None,
) -> Transition:
    """查表；找不到则 IllegalTransitionError。

    hitl_approved 无静态目标：应抛 IllegalTransitionError，提示走 send。
    """
    # TODO
    raise NotImplementedError


def map_reflection_decision(decision: str) -> str:
    """把 Day68 决策字面量映射为 FSM 事件。"""
    # TODO: 查 DECISION_TO_EVENT；未知决策抛 ValueError
    raise NotImplementedError


@dataclass
class AgentStateMachine:
    """可运行的 Agent 状态机。"""

    state: str = STATE_IDLE
    history: list[TransitionRecord] = field(default_factory=list)
    hitl_resume: str | None = None
    transitions: tuple[Transition, ...] = field(default_factory=default_transitions)

    def __post_init__(self) -> None:
        if self.state not in VALID_STATES:
            raise ValueError(f"invalid state: {self.state}")
        if self.hitl_resume is not None and self.hitl_resume not in VALID_STATES:
            raise ValueError(f"invalid hitl_resume: {self.hitl_resume}")
        object.__setattr__(self, "transitions", tuple(self.transitions))
        build_transition_map(self.transitions)  # 校验无重复

    def send(self, event: str) -> str:
        """发送事件并转移；返回新状态。

        规则：
        1. awaiting_hitl + hitl_approved → 跳到 hitl_resume（清空 resume）
        2. need_hitl → 按 HITL_RESUME_DEFAULT 记录 resume，再进入 awaiting_hitl
        3. hitl_rejected / reset → 清空 hitl_resume
        4. 其他事件走 lookup_transition
        """
        # TODO
        raise NotImplementedError

    def send_decision(self, decision: str) -> str:
        """便捷：发送 Reflection 决策。"""
        # TODO: 复用 map_reflection_decision + send
        raise NotImplementedError

    def is_terminal(self) -> bool:
        # TODO
        raise NotImplementedError

    def snapshot(self) -> dict[str, object]:
        """返回 state / hitl_resume / steps / terminal / path。"""
        # TODO: path = 起始态 + 每次 to_state
        raise NotImplementedError


def apply_events(
    events: Sequence[str],
    *,
    machine: AgentStateMachine | None = None,
) -> AgentStateMachine:
    """按序发送事件。"""
    # TODO
    raise NotImplementedError


def simulate_happy_path() -> AgentStateMachine:
    """主路径：规划 → 执行 → 反思接受 → done。"""
    # TODO
    raise NotImplementedError


def simulate_retry_then_accept() -> AgentStateMachine:
    """反思要求重试一次后再接受。"""
    # TODO
    raise NotImplementedError


def simulate_revise_loop() -> AgentStateMachine:
    """反思要求改计划，再走通主路径。"""
    # TODO
    raise NotImplementedError


def simulate_abort_on_reflect() -> AgentStateMachine:
    """反思直接中止。"""
    # TODO
    raise NotImplementedError


def simulate_hitl_approve() -> AgentStateMachine:
    """规划阶段人审通过，再完成。"""
    # TODO: goal → need_hitl → approved → execution_finished → accept
    raise NotImplementedError


def simulate_hitl_reject() -> AgentStateMachine:
    """执行中人审拒绝 → aborted。"""
    # TODO
    raise NotImplementedError


def build_demo_machines() -> list[AgentStateMachine]:
    """至少 5 条不同情景。"""
    # TODO
    raise NotImplementedError


def summarize_machine(machine: AgentStateMachine) -> dict[str, object]:
    """汇总单机轨迹。"""
    # TODO: final_state / steps / terminal / hitl_resume / path / events
    raise NotImplementedError


def render_trace(machine: AgentStateMachine) -> str:
    """把转移历史渲染成 Markdown。"""
    # TODO
    raise NotImplementedError


def render_mermaid(transitions: Sequence[Transition] | None = None) -> str:
    """由转移表生成 Mermaid stateDiagram-v2。

    另按 HITL_RESUME_DEFAULT 展开 hitl_approved 恢复边。
    开头包含 `stateDiagram-v2` 与 `[*] --> idle`。
    """
    # TODO
    raise NotImplementedError


def render_ascii_overview() -> str:
    """主路径 ASCII 概览。"""
    # TODO: 返回非空多行字符串即可；报告会引用
    raise NotImplementedError


def run_demo_machines(
    machines: Sequence[AgentStateMachine] | None = None,
) -> list[dict[str, object]]:
    """批量演示并汇总。"""
    # TODO
    raise NotImplementedError


def render_state_machine_report(
    machines: Sequence[AgentStateMachine] | None = None,
) -> str:
    """生成含固定二级标题的学习报告。"""
    # TODO: 必须包含 REQUIRED_REPORT_SECTIONS 中每个标题（作 ## 二级标题）
    raise NotImplementedError
