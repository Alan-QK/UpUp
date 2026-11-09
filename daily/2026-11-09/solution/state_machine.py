"""Day 69 参考实现：Agent 状态机（Plan / Execute / Reflect / HITL）。

用转移表描述生命周期；send(event) 驱动跳转；同一份表渲染 Mermaid。
不调用 LLM，聚焦建模与可测试性。
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
    """今日默认 Agent 生命周期转移表。"""
    return (
        Transition(STATE_IDLE, EVENT_GOAL_RECEIVED, STATE_PLANNING, "收到目标，开始规划"),
        Transition(STATE_PLANNING, EVENT_PLAN_READY, STATE_EXECUTING, "计划就绪，开始执行"),
        Transition(
            STATE_PLANNING,
            EVENT_NEED_HITL,
            STATE_AWAITING_HITL,
            "计划需人审",
        ),
        Transition(
            STATE_PLANNING,
            EVENT_DECISION_ABORT,
            STATE_ABORTED,
            "规划阶段中止",
        ),
        Transition(
            STATE_EXECUTING,
            EVENT_EXECUTION_FINISHED,
            STATE_REFLECTING,
            "执行结束，进入反思",
        ),
        Transition(
            STATE_EXECUTING,
            EVENT_NEED_HITL,
            STATE_AWAITING_HITL,
            "执行中需人审",
        ),
        Transition(
            STATE_EXECUTING,
            EVENT_DECISION_ABORT,
            STATE_ABORTED,
            "执行阶段中止",
        ),
        Transition(
            STATE_REFLECTING,
            EVENT_DECISION_ACCEPT,
            STATE_DONE,
            "评审通过",
        ),
        Transition(
            STATE_REFLECTING,
            EVENT_DECISION_RETRY,
            STATE_EXECUTING,
            "重试薄弱步骤",
        ),
        Transition(
            STATE_REFLECTING,
            EVENT_DECISION_REVISE,
            STATE_PLANNING,
            "回到规划改计划",
        ),
        Transition(
            STATE_REFLECTING,
            EVENT_DECISION_ABORT,
            STATE_ABORTED,
            "评审决定中止",
        ),
        Transition(
            STATE_REFLECTING,
            EVENT_NEED_HITL,
            STATE_AWAITING_HITL,
            "交付前需人审",
        ),
        # hitl_approved 目标由运行时 hitl_resume 决定，不进静态表
        Transition(
            STATE_AWAITING_HITL,
            EVENT_HITL_REJECTED,
            STATE_ABORTED,
            "人审拒绝",
        ),
        Transition(STATE_DONE, EVENT_RESET, STATE_IDLE, "复位"),
        Transition(STATE_ABORTED, EVENT_RESET, STATE_IDLE, "复位"),
    )


def build_transition_map(
    transitions: Sequence[Transition] | None = None,
) -> dict[tuple[str, str], Transition]:
    """(source, event) → Transition；重复键抛错。"""
    items = list(transitions) if transitions is not None else list(default_transitions())
    mapping: dict[tuple[str, str], Transition] = {}
    for t in items:
        if not isinstance(t, Transition):
            raise TypeError("transitions must contain Transition")
        key = (t.source, t.event)
        if key in mapping:
            raise ValueError(f"duplicate transition: {key}")
        mapping[key] = t
    return mapping


def list_events_from(state: str, transitions: Sequence[Transition] | None = None) -> list[str]:
    """列出某状态下合法事件（排序后）。"""
    if state not in VALID_STATES:
        raise ValueError(f"invalid state: {state}")
    mapping = build_transition_map(transitions)
    events = {event for (src, event) in mapping if src == state}
    # 动态边：人审通过
    if state == STATE_AWAITING_HITL:
        events.add(EVENT_HITL_APPROVED)
    return sorted(events)


def can_transition(
    state: str,
    event: str,
    transitions: Sequence[Transition] | None = None,
) -> bool:
    """是否存在 (state, event) 转移（含 hitl_approved 动态边）。"""
    if state not in VALID_STATES or event not in VALID_EVENTS:
        return False
    if state == STATE_AWAITING_HITL and event == EVENT_HITL_APPROVED:
        return True
    return (state, event) in build_transition_map(transitions)


def lookup_transition(
    state: str,
    event: str,
    transitions: Sequence[Transition] | None = None,
) -> Transition:
    """查表；找不到则 IllegalTransitionError。

    注意：`hitl_approved` 无静态目标，请走 `AgentStateMachine.send`。
    """
    if state not in VALID_STATES:
        raise ValueError(f"invalid state: {state}")
    if event not in VALID_EVENTS:
        raise ValueError(f"invalid event: {event}")
    if state == STATE_AWAITING_HITL and event == EVENT_HITL_APPROVED:
        raise IllegalTransitionError(
            "hitl_approved is dynamic; use AgentStateMachine.send"
        )
    mapping = build_transition_map(transitions)
    key = (state, event)
    if key not in mapping:
        raise IllegalTransitionError(f"illegal transition: {state} + {event}")
    return mapping[key]


def map_reflection_decision(decision: str) -> str:
    """把 Day68 决策字面量映射为 FSM 事件。"""
    if not isinstance(decision, str) or not decision.strip():
        raise ValueError("decision must be non-empty str")
    key = decision.strip().lower()
    if key not in DECISION_TO_EVENT:
        raise ValueError(f"unknown decision: {decision}")
    return DECISION_TO_EVENT[key]


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
        # 冻结转移表副本，避免外部篡改
        object.__setattr__(self, "transitions", tuple(self.transitions))
        build_transition_map(self.transitions)  # 校验无重复

    def send(self, event: str) -> str:
        """发送事件并转移；返回新状态。"""
        if event not in VALID_EVENTS:
            raise ValueError(f"invalid event: {event}")

        # HITL 批准：跳到挂起时记录的 resume
        if self.state == STATE_AWAITING_HITL and event == EVENT_HITL_APPROVED:
            if self.hitl_resume is None or self.hitl_resume not in VALID_STATES:
                raise IllegalTransitionError(
                    "hitl_approved requires a valid hitl_resume"
                )
            target = self.hitl_resume
            note = f"人审通过，恢复到 {target}"
            record = TransitionRecord(self.state, event, target, note)
            self.state = target
            self.hitl_resume = None
            self.history.append(record)
            return self.state

        tr = lookup_transition(self.state, event, self.transitions)

        # 进入 HITL：记下批准后应去哪
        if event == EVENT_NEED_HITL:
            resume = HITL_RESUME_DEFAULT.get(self.state)
            if resume is None:
                raise IllegalTransitionError(
                    f"no hitl_resume default for state={self.state}"
                )
            self.hitl_resume = resume

        if event in {EVENT_HITL_REJECTED, EVENT_RESET}:
            self.hitl_resume = None

        record = TransitionRecord(self.state, event, tr.target, tr.note)
        self.state = tr.target
        self.history.append(record)
        return self.state

    def send_decision(self, decision: str) -> str:
        """便捷：发送 Reflection 决策。"""
        return self.send(map_reflection_decision(decision))

    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    def snapshot(self) -> dict[str, object]:
        return {
            "state": self.state,
            "hitl_resume": self.hitl_resume,
            "steps": len(self.history),
            "terminal": self.is_terminal(),
            "path": [STATE_IDLE] + [r.to_state for r in self.history]
            if not self.history
            else [self.history[0].from_state] + [r.to_state for r in self.history],
        }


def apply_events(
    events: Sequence[str],
    *,
    machine: AgentStateMachine | None = None,
) -> AgentStateMachine:
    """按序发送事件。"""
    m = machine if machine is not None else AgentStateMachine()
    for ev in events:
        m.send(ev)
    return m


def simulate_happy_path() -> AgentStateMachine:
    """主路径：规划 → 执行 → 反思接受 → done。"""
    return apply_events(
        [
            EVENT_GOAL_RECEIVED,
            EVENT_PLAN_READY,
            EVENT_EXECUTION_FINISHED,
            EVENT_DECISION_ACCEPT,
        ]
    )


def simulate_retry_then_accept() -> AgentStateMachine:
    """反思要求重试一次后再接受。"""
    return apply_events(
        [
            EVENT_GOAL_RECEIVED,
            EVENT_PLAN_READY,
            EVENT_EXECUTION_FINISHED,
            EVENT_DECISION_RETRY,
            EVENT_EXECUTION_FINISHED,
            EVENT_DECISION_ACCEPT,
        ]
    )


def simulate_revise_loop() -> AgentStateMachine:
    """反思要求改计划，再走通主路径。"""
    return apply_events(
        [
            EVENT_GOAL_RECEIVED,
            EVENT_PLAN_READY,
            EVENT_EXECUTION_FINISHED,
            EVENT_DECISION_REVISE,
            EVENT_PLAN_READY,
            EVENT_EXECUTION_FINISHED,
            EVENT_DECISION_ACCEPT,
        ]
    )


def simulate_abort_on_reflect() -> AgentStateMachine:
    """反思直接中止。"""
    return apply_events(
        [
            EVENT_GOAL_RECEIVED,
            EVENT_PLAN_READY,
            EVENT_EXECUTION_FINISHED,
            EVENT_DECISION_ABORT,
        ]
    )


def simulate_hitl_approve() -> AgentStateMachine:
    """执行前计划人审通过，再完成。"""
    return apply_events(
        [
            EVENT_GOAL_RECEIVED,
            EVENT_NEED_HITL,
            EVENT_HITL_APPROVED,
            EVENT_EXECUTION_FINISHED,
            EVENT_DECISION_ACCEPT,
        ]
    )


def simulate_hitl_reject() -> AgentStateMachine:
    """人审拒绝 → aborted。"""
    return apply_events(
        [
            EVENT_GOAL_RECEIVED,
            EVENT_PLAN_READY,
            EVENT_NEED_HITL,
            EVENT_HITL_REJECTED,
        ]
    )


def build_demo_machines() -> list[AgentStateMachine]:
    """至少 5 条不同情景。"""
    return [
        simulate_happy_path(),
        simulate_retry_then_accept(),
        simulate_revise_loop(),
        simulate_abort_on_reflect(),
        simulate_hitl_approve(),
        simulate_hitl_reject(),
    ]


def summarize_machine(machine: AgentStateMachine) -> dict[str, object]:
    """汇总单机轨迹。"""
    if not isinstance(machine, AgentStateMachine):
        raise TypeError("machine must be AgentStateMachine")
    snap = machine.snapshot()
    return {
        "final_state": machine.state,
        "steps": snap["steps"],
        "terminal": snap["terminal"],
        "hitl_resume": machine.hitl_resume,
        "path": snap["path"],
        "events": [r.event for r in machine.history],
    }


def render_trace(machine: AgentStateMachine) -> str:
    """把转移历史渲染成 Markdown。"""
    if not isinstance(machine, AgentStateMachine):
        raise TypeError("machine must be AgentStateMachine")
    lines = [
        f"# 状态轨迹 → `{machine.state}`",
        "",
        f"- 步数：{len(machine.history)}",
        f"- 终态：{'是' if machine.is_terminal() else '否'}",
        f"- hitl_resume：{machine.hitl_resume or '—'}",
        "",
    ]
    if not machine.history:
        lines.append("_（尚无转移）_")
        lines.append("")
        return "\n".join(lines)

    lines.append("| # | From | Event | To | Note |")
    lines.append("|---|------|-------|----|------|")
    for i, r in enumerate(machine.history, start=1):
        note = r.note.replace("|", "\\|") if r.note else "—"
        lines.append(
            f"| {i} | `{r.from_state}` | `{r.event}` | `{r.to_state}` | {note} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_mermaid(transitions: Sequence[Transition] | None = None) -> str:
    """由转移表生成 Mermaid stateDiagram-v2。

    `hitl_approved` 按 HITL_RESUME_DEFAULT 展开为多条可能恢复边。
    """
    items = list(transitions) if transitions is not None else list(default_transitions())
    lines = [
        "stateDiagram-v2",
        "    [*] --> idle",
        "    done --> [*]",
        "    aborted --> [*]",
    ]
    seen: set[tuple[str, str, str]] = set()
    for t in items:
        key = (t.source, t.event, t.target)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"    {t.source} --> {t.target}: {t.event}")

    for resume in sorted(set(HITL_RESUME_DEFAULT.values())):
        key = (STATE_AWAITING_HITL, EVENT_HITL_APPROVED, resume)
        if key in seen:
            continue
        seen.add(key)
        lines.append(
            f"    {STATE_AWAITING_HITL} --> {resume}: {EVENT_HITL_APPROVED}"
        )
    lines.append("")
    return "\n".join(lines)


def render_ascii_overview() -> str:
    """主路径 ASCII 概览（辅助阅读，完整边以 Mermaid 为准）。"""
    return "\n".join(
        [
            "idle",
            "  | goal_received",
            "  v",
            "planning ----need_hitl----> awaiting_hitl",
            "  | plan_ready                  | hitl_approved / hitl_rejected",
            "  v                             v",
            "executing <---decision_retry--- reflecting ---> done",
            "  | execution_finished            | decision_revise",
            "  +--------> reflecting           v",
            "                |              planning",
            "                +--decision_abort--> aborted",
            "",
        ]
    )


def run_demo_machines(
    machines: Sequence[AgentStateMachine] | None = None,
) -> list[dict[str, object]]:
    """批量演示并汇总。"""
    items = list(machines) if machines is not None else build_demo_machines()
    return [summarize_machine(m) for m in items]


def render_state_machine_report(
    machines: Sequence[AgentStateMachine] | None = None,
) -> str:
    """生成含固定二级标题的学习报告。"""
    items = list(machines) if machines is not None else build_demo_machines()
    summaries = [summarize_machine(m) for m in items]
    done_n = sum(1 for s in summaries if s["final_state"] == STATE_DONE)
    aborted_n = sum(1 for s in summaries if s["final_state"] == STATE_ABORTED)
    other_n = len(summaries) - done_n - aborted_n
    sample = items[0] if items else AgentStateMachine()
    mermaid = render_mermaid()

    lines = [
        "# Day 69 报告｜状态机视角",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[0]}",
        "",
        "Agent 状态机 = **显式状态** + **事件** + **转移表**。",
        "把 Plan / Execute / Reflect / HITL 从调用栈里拎出来，变成可测试、可画图的生命周期。",
        "前端熟悉的 XState / Redux 心智在这里完全通用。",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[1]}",
        "",
        "七态：`idle` / `planning` / `executing` / `reflecting` / "
        "`awaiting_hitl` / `done` / `aborted`。",
        "主路径：`idle → planning → executing → reflecting → done`。",
        "纠错：`decision_retry→executing`，`decision_revise→planning`，"
        "`decision_abort→aborted`。",
        "",
        "```text",
        render_ascii_overview().rstrip(),
        "```",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[2]}",
        "",
        f"- 情景数：{len(summaries)}",
        f"- done：{done_n} · aborted：{aborted_n} · 其他：{other_n}",
        "",
        "### 样例轨迹（happy path）",
        "",
        render_trace(sample),
        f"## {REQUIRED_REPORT_SECTIONS[3]}",
        "",
        "```mermaid",
        mermaid.rstrip(),
        "```",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[4]}",
        "",
        "Day 70｜周挑战：多步研究任务——串起计划、执行、反思与状态机，做出可展示闭环。",
        "",
    ]
    return "\n".join(lines)
