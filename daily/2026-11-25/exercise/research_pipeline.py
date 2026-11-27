"""Day 70 练习：多步研究任务（Plan → Execute → Reflect → Done）。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——不调用 LLM。

本周拼装：
- Day 66 Planner → build_research_plan
- Day 67 Executor → execute_plan（mock 工具）
- Day 68 Reflection → critique_trace / apply_retry
- Day 69 FSM → 事件驱动 state_path
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Sequence

# --- 计划模型 ---

STEP_KIND_CLARIFY = "clarify"
STEP_KIND_RESEARCH = "research"
STEP_KIND_ANALYZE = "analyze"
STEP_KIND_DELIVER = "deliver"
VALID_STEP_KINDS = frozenset(
    {
        STEP_KIND_CLARIFY,
        STEP_KIND_RESEARCH,
        STEP_KIND_ANALYZE,
        STEP_KIND_DELIVER,
    }
)

KIND_TO_TOOL: dict[str, str] = {
    STEP_KIND_CLARIFY: "clarify_goal",
    STEP_KIND_RESEARCH: "search_notes",
    STEP_KIND_ANALYZE: "analyze_findings",
    STEP_KIND_DELIVER: "write_deliverable",
}

MIN_GOAL_LEN = 4
DEFAULT_MAX_STEPS = 5
MIN_MAX_STEPS = 3
MAX_MAX_STEPS = 8

# --- 执行状态 ---

STATUS_DONE = "done"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"
VALID_STATUSES = frozenset({STATUS_DONE, STATUS_FAILED, STATUS_SKIPPED})

STOP_COMPLETED = "completed"
STOP_FAILED = "failed"
VALID_STOP_REASONS = frozenset({STOP_COMPLETED, STOP_FAILED})

# --- 反思决策 ---

DECISION_ACCEPT = "accept"
DECISION_RETRY = "retry"
DECISION_ABORT = "abort"
VALID_DECISIONS = frozenset({DECISION_ACCEPT, DECISION_RETRY, DECISION_ABORT})

MIN_OBS_LEN = 12
DEFAULT_MAX_ROUNDS = 2

# --- 状态机 ---

STATE_IDLE = "idle"
STATE_PLANNING = "planning"
STATE_EXECUTING = "executing"
STATE_REFLECTING = "reflecting"
STATE_DONE = "done"
STATE_ABORTED = "aborted"
VALID_STATES = frozenset(
    {
        STATE_IDLE,
        STATE_PLANNING,
        STATE_EXECUTING,
        STATE_REFLECTING,
        STATE_DONE,
        STATE_ABORTED,
    }
)

EVENT_GOAL_RECEIVED = "goal_received"
EVENT_PLAN_READY = "plan_ready"
EVENT_EXECUTION_FINISHED = "execution_finished"
EVENT_DECISION_ACCEPT = "decision_accept"
EVENT_DECISION_RETRY = "decision_retry"
EVENT_DECISION_ABORT = "decision_abort"

DECISION_TO_EVENT: dict[str, str] = {
    DECISION_ACCEPT: EVENT_DECISION_ACCEPT,
    DECISION_RETRY: EVENT_DECISION_RETRY,
    DECISION_ABORT: EVENT_DECISION_ABORT,
}

REQUIRED_REPORT_SECTIONS = (
    "何为多步研究任务",
    "本周能力拼装",
    "计划与执行展示",
    "今日演示统计",
    "下周预告",
)

_RESEARCH_HINT = re.compile(
    r"(调研|研究|对比|比较|选型|评估|investigate|research|compare)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PlanStep:
    """研究计划中的一步。"""

    id: str
    title: str
    detail: str
    kind: str
    depends_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("id must be non-empty str")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be non-empty str")
        if not isinstance(self.detail, str):
            raise TypeError("detail must be str")
        if self.kind not in VALID_STEP_KINDS:
            raise ValueError(f"invalid step kind: {self.kind}")
        if not isinstance(self.depends_on, tuple):
            raise TypeError("depends_on must be tuple")


@dataclass(frozen=True)
class Plan:
    """可展示的研究计划。"""

    goal: str
    steps: tuple[PlanStep, ...]
    strategy: str = "research_template"

    def __post_init__(self) -> None:
        if not isinstance(self.goal, str) or not self.goal.strip():
            raise ValueError("goal must be non-empty str")
        if not isinstance(self.steps, tuple) or not self.steps:
            raise ValueError("steps must be non-empty tuple")
        if not isinstance(self.strategy, str) or not self.strategy.strip():
            raise ValueError("strategy must be non-empty str")
        ids = [s.id for s in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("step ids must be unique")
        known = set(ids)
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in known:
                    raise ValueError(f"unknown dependency: {dep}")
                if dep == step.id:
                    raise ValueError("step cannot depend on itself")


@dataclass(frozen=True)
class StepResult:
    """单步执行结果。"""

    step_id: str
    status: str
    tool_name: str
    observation: str = ""
    error: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.step_id, str) or not self.step_id.strip():
            raise ValueError("step_id must be non-empty str")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"invalid status: {self.status}")
        if not isinstance(self.tool_name, str):
            raise TypeError("tool_name must be str")
        if not isinstance(self.observation, str):
            raise TypeError("observation must be str")
        if not isinstance(self.error, str):
            raise TypeError("error must be str")


@dataclass
class ExecutionTrace:
    """一次执行的轨迹。"""

    goal: str
    results: list[StepResult] = field(default_factory=list)
    stop_reason: str = STOP_COMPLETED
    deliverable: str = ""
    context: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.goal, str) or not self.goal.strip():
            raise ValueError("goal must be non-empty str")
        if self.stop_reason not in VALID_STOP_REASONS:
            raise ValueError(f"invalid stop_reason: {self.stop_reason}")


@dataclass(frozen=True)
class Critique:
    """一轮评审。"""

    decision: str
    rationale: str
    weak_step_id: str | None = None

    def __post_init__(self) -> None:
        if self.decision not in VALID_DECISIONS:
            raise ValueError(f"invalid decision: {self.decision}")
        if not isinstance(self.rationale, str) or not self.rationale.strip():
            raise ValueError("rationale must be non-empty str")


@dataclass
class ResearchRun:
    """一次完整研究任务运行结果（可展示）。"""

    goal: str
    plan: Plan
    trace: ExecutionTrace
    decision: str
    state_path: list[str]
    rounds: int
    critiques: list[Critique] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.decision not in VALID_DECISIONS:
            raise ValueError(f"invalid decision: {self.decision}")
        if self.rounds < 1:
            raise ValueError("rounds must be >= 1")


def normalize_goal(text: str) -> str:
    """去掉首尾空白、压缩中间空白。"""
    # TODO
    raise NotImplementedError


def build_research_plan(goal: str, *, max_steps: int = DEFAULT_MAX_STEPS) -> Plan:
    """把调研目标拆成串行步骤（澄清 → 检索 → 分析 → 交付）。

    规则：
    - normalize 后长度 < MIN_GOAL_LEN → ValueError
    - max_steps 夹到 [MIN_MAX_STEPS, MAX_MAX_STEPS]
    - 默认 4 步；若 max_steps == 3 则合并分析进交付，变成 3 步
    - 步骤 id 为 S1..Sn，依赖默认串行
    - strategy 固定 research_template
    """
    # TODO
    raise NotImplementedError


def _mock_observation(step: PlanStep, goal: str, context: dict[str, object]) -> str:
    """确定性 mock 观察（已给齐，勿改签名）。"""
    tool = KIND_TO_TOOL[step.kind]
    if step.kind == STEP_KIND_CLARIFY:
        scope = f"范围：围绕「{goal}」收集候选、对比维度与约束。"
        context["scope"] = scope
        return f"[{tool}] 已澄清。{scope}"
    if step.kind == STEP_KIND_RESEARCH:
        notes = [
            "候选A：开源嵌入友好、本地可跑",
            "候选B：托管服务、运维成本更低",
            "候选C：与现有 PG 生态整合方便",
        ]
        context["notes"] = notes
        joined = "；".join(notes)
        return f"[{tool}] 检索到 3 条笔记：{joined}"
    if step.kind == STEP_KIND_ANALYZE:
        notes = context.get("notes")
        if not isinstance(notes, list) or not notes:
            return f"[{tool}] 缺少检索材料，分析中止提示。"
        summary = (
            f"对比完成：共 {len(notes)} 个候选；"
            "建议按「本地优先 / 托管优先 / SQL 亲和」三维打分。"
        )
        context["analysis"] = summary
        return f"[{tool}] {summary}"
    # deliver
    analysis = context.get("analysis")
    notes = context.get("notes")
    n = len(notes) if isinstance(notes, list) else 0
    body = analysis if isinstance(analysis, str) and analysis.strip() else (
        f"基于 {n} 条笔记给出初步选型建议：先试点本地方案，再评估托管。"
    )
    deliverable = f"交付摘要｜目标：{goal}\n{body}\n下一步：做一页对比表与 PoC 清单。"
    context["deliverable"] = deliverable
    return f"[{tool}] {deliverable}"


def execute_plan(
    plan: Plan,
    *,
    fail_step_id: str | None = None,
) -> ExecutionTrace:
    """按计划逐步调用 mock 工具。

    规则：
    - 依赖必须全部 STATUS_DONE，否则当前步 SKIPPED，后续也跳过，stop=failed
    - fail_step_id 命中时该步 FAILED（error 非空），后续 SKIPPED，stop=failed
    - 全部成功：stop=completed，并把 context['deliverable'] 写入 trace.deliverable
    """
    # TODO
    raise NotImplementedError


def critique_trace(trace: ExecutionTrace) -> Critique:
    """启发式评审。

    优先级：
    1. 任意 FAILED → retry（weak_step_id=第一个 failed）
    2. stop_reason=failed 或无 deliverable → retry（weak 取第一个非 done，或最后一步）
    3. 任意 done 但 observation 过短（< MIN_OBS_LEN）→ retry
    4. 否则 accept
    不在今日产出 abort（留给管线 max_rounds 耗尽）。
    """
    # TODO
    raise NotImplementedError


def apply_retry(plan: Plan, trace: ExecutionTrace, critique: Critique) -> ExecutionTrace:
    """模拟重试：清掉失败，重新 execute_plan（不再注入 fail）。"""
    # TODO: 忽略 critique.weak_step_id 细节亦可；关键是第二轮不再 fail
    raise NotImplementedError


def _transition(state: str, event: str) -> str:
    """最小转移表（已给齐）。"""
    table: dict[tuple[str, str], str] = {
        (STATE_IDLE, EVENT_GOAL_RECEIVED): STATE_PLANNING,
        (STATE_PLANNING, EVENT_PLAN_READY): STATE_EXECUTING,
        (STATE_EXECUTING, EVENT_EXECUTION_FINISHED): STATE_REFLECTING,
        (STATE_REFLECTING, EVENT_DECISION_ACCEPT): STATE_DONE,
        (STATE_REFLECTING, EVENT_DECISION_RETRY): STATE_EXECUTING,
        (STATE_REFLECTING, EVENT_DECISION_ABORT): STATE_ABORTED,
    }
    key = (state, event)
    if key not in table:
        raise ValueError(f"illegal transition: {state} + {event}")
    return table[key]


def run_research_task(
    goal: str,
    *,
    max_steps: int = DEFAULT_MAX_STEPS,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    inject_fail_step: str | None = None,
) -> ResearchRun:
    """编排完整研究任务，返回可展示结果。

    流程：
    1. idle --goal_received--> planning；build_research_plan
    2. plan_ready → executing；execute_plan（仅第 1 轮使用 inject_fail_step）
    3. execution_finished → reflecting；critique_trace
    4. accept → done；retry → 回到 executing（apply_retry）；超出 max_rounds → abort
    记录完整 state_path（含起始 idle）。
    """
    # TODO
    raise NotImplementedError


def render_plan(plan: Plan) -> str:
    """把计划渲染成 Markdown。"""
    # TODO
    raise NotImplementedError


def render_execution(trace: ExecutionTrace) -> str:
    """把执行轨迹渲染成 Markdown 表格。"""
    # TODO
    raise NotImplementedError


def summarize_run(run: ResearchRun) -> dict[str, object]:
    """汇总单次运行。"""
    # TODO: goal / decision / rounds / steps / stop_reason / has_deliverable / state_path
    raise NotImplementedError


def build_demo_runs() -> list[ResearchRun]:
    """至少 2 条：happy path + 注入失败后 retry 成功。"""
    # TODO
    raise NotImplementedError


def render_research_report(runs: Sequence[ResearchRun] | None = None) -> str:
    """生成含固定二级标题的学习报告。"""
    # TODO: 必须包含 REQUIRED_REPORT_SECTIONS 中每个标题（作 ## 二级标题）
    # 报告中要展示至少一份 plan 与一份 execution
    raise NotImplementedError
