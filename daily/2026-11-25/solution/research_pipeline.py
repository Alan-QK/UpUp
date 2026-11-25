"""Day 70 参考实现：多步研究任务（Plan → Execute → Reflect → Done）。

串起本周 Planner / Executor / Reflection / FSM，输出可展示计划与执行轨迹。
不调用 LLM，工具与评审均为确定性启发式。
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
    if not isinstance(text, str):
        raise TypeError("goal must be str")
    return re.sub(r"\s+", " ", text.strip())


def build_research_plan(goal: str, *, max_steps: int = DEFAULT_MAX_STEPS) -> Plan:
    """把调研目标拆成串行步骤（澄清 → 检索 → 分析 → 交付）。"""
    cleaned = normalize_goal(goal)
    if len(cleaned) < MIN_GOAL_LEN:
        raise ValueError(f"goal too short (< {MIN_GOAL_LEN})")
    if not isinstance(max_steps, int) or isinstance(max_steps, bool):
        raise TypeError("max_steps must be int")
    limit = max(MIN_MAX_STEPS, min(MAX_MAX_STEPS, max_steps))

    # 提示：含调研关键词更「像」研究任务；不含也允许（教学放宽）
    _ = bool(_RESEARCH_HINT.search(cleaned))

    if limit <= 3:
        raw = [
            (
                STEP_KIND_CLARIFY,
                "澄清调研边界",
                f"明确「{cleaned}」的范围、受众与成功标准。",
            ),
            (
                STEP_KIND_RESEARCH,
                "检索候选材料",
                "从笔记/资料中收集候选方案与关键事实。",
            ),
            (
                STEP_KIND_DELIVER,
                "分析并输出建议",
                "合并对比结论，输出可交付的选型摘要。",
            ),
        ]
    else:
        raw = [
            (
                STEP_KIND_CLARIFY,
                "澄清调研边界",
                f"明确「{cleaned}」的范围、受众与成功标准。",
            ),
            (
                STEP_KIND_RESEARCH,
                "检索候选材料",
                "从笔记/资料中收集候选方案与关键事实。",
            ),
            (
                STEP_KIND_ANALYZE,
                "对比分析",
                "按维度对比候选，形成取舍建议。",
            ),
            (
                STEP_KIND_DELIVER,
                "输出选型建议",
                "汇总为可展示的交付摘要与下一步。",
            ),
        ]
        if limit >= 5:
            # 可选第 5 步：在检索后加一轮「补充检索」感的 analyze 前奏——
            # 为控制复杂度，仍保持 4 步；limit 只作上限裁剪。
            raw = raw[:limit]

    steps: list[PlanStep] = []
    for i, (kind, title, detail) in enumerate(raw, start=1):
        sid = f"S{i}"
        deps: tuple[str, ...] = (f"S{i - 1}",) if i > 1 else ()
        steps.append(
            PlanStep(id=sid, title=title, detail=detail, kind=kind, depends_on=deps)
        )
    return Plan(goal=cleaned, steps=tuple(steps), strategy="research_template")


def _mock_observation(step: PlanStep, goal: str, context: dict[str, object]) -> str:
    """确定性 mock 观察。"""
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
    analysis = context.get("analysis")
    notes = context.get("notes")
    n = len(notes) if isinstance(notes, list) else 0
    body = (
        analysis
        if isinstance(analysis, str) and analysis.strip()
        else f"基于 {n} 条笔记给出初步选型建议：先试点本地方案，再评估托管。"
    )
    deliverable = f"交付摘要｜目标：{goal}\n{body}\n下一步：做一页对比表与 PoC 清单。"
    context["deliverable"] = deliverable
    return f"[{tool}] {deliverable}"


def execute_plan(
    plan: Plan,
    *,
    fail_step_id: str | None = None,
) -> ExecutionTrace:
    """按计划逐步调用 mock 工具。"""
    if not isinstance(plan, Plan):
        raise TypeError("plan must be Plan")
    if fail_step_id is not None and (
        not isinstance(fail_step_id, str) or not fail_step_id.strip()
    ):
        raise ValueError("fail_step_id must be non-empty str or None")

    trace = ExecutionTrace(goal=plan.goal)
    status_by_id: dict[str, str] = {}
    skip_rest = False

    for step in plan.steps:
        tool = KIND_TO_TOOL[step.kind]

        if skip_rest:
            result = StepResult(
                step_id=step.id,
                status=STATUS_SKIPPED,
                tool_name=tool,
                observation="",
                error="skipped after upstream failure",
            )
            trace.results.append(result)
            status_by_id[step.id] = STATUS_SKIPPED
            continue

        deps_ok = all(status_by_id.get(dep) == STATUS_DONE for dep in step.depends_on)
        if not deps_ok:
            result = StepResult(
                step_id=step.id,
                status=STATUS_SKIPPED,
                tool_name=tool,
                observation="",
                error="dependency not satisfied",
            )
            trace.results.append(result)
            status_by_id[step.id] = STATUS_SKIPPED
            skip_rest = True
            trace.stop_reason = STOP_FAILED
            continue

        if fail_step_id is not None and step.id == fail_step_id:
            result = StepResult(
                step_id=step.id,
                status=STATUS_FAILED,
                tool_name=tool,
                observation="",
                error=f"injected failure at {step.id}",
            )
            trace.results.append(result)
            status_by_id[step.id] = STATUS_FAILED
            skip_rest = True
            trace.stop_reason = STOP_FAILED
            continue

        obs = _mock_observation(step, plan.goal, trace.context)
        result = StepResult(
            step_id=step.id,
            status=STATUS_DONE,
            tool_name=tool,
            observation=obs,
        )
        trace.results.append(result)
        status_by_id[step.id] = STATUS_DONE

    if trace.stop_reason == STOP_COMPLETED:
        deliverable = trace.context.get("deliverable")
        if isinstance(deliverable, str):
            trace.deliverable = deliverable
    return trace


def critique_trace(trace: ExecutionTrace) -> Critique:
    """启发式评审。"""
    if not isinstance(trace, ExecutionTrace):
        raise TypeError("trace must be ExecutionTrace")

    failed = [r for r in trace.results if r.status == STATUS_FAILED]
    if failed:
        weak = failed[0].step_id
        return Critique(
            decision=DECISION_RETRY,
            rationale=f"步骤 {weak} 失败，需要重试",
            weak_step_id=weak,
        )

    if trace.stop_reason == STOP_FAILED or not trace.deliverable.strip():
        weak = next(
            (r.step_id for r in trace.results if r.status != STATUS_DONE),
            trace.results[-1].step_id if trace.results else None,
        )
        return Critique(
            decision=DECISION_RETRY,
            rationale="执行未完成或缺少 deliverable，需要重试",
            weak_step_id=weak,
        )

    short = [
        r
        for r in trace.results
        if r.status == STATUS_DONE and len(r.observation.strip()) < MIN_OBS_LEN
    ]
    if short:
        weak = short[0].step_id
        return Critique(
            decision=DECISION_RETRY,
            rationale=f"步骤 {weak} 观察过短，需要重试补全",
            weak_step_id=weak,
        )

    return Critique(
        decision=DECISION_ACCEPT,
        rationale="轨迹完整且含交付物，接受结果",
        weak_step_id=None,
    )


def apply_retry(plan: Plan, trace: ExecutionTrace, critique: Critique) -> ExecutionTrace:
    """模拟重试：清掉失败，重新 execute_plan（不再注入 fail）。"""
    if not isinstance(plan, Plan):
        raise TypeError("plan must be Plan")
    if not isinstance(trace, ExecutionTrace):
        raise TypeError("trace must be ExecutionTrace")
    if not isinstance(critique, Critique):
        raise TypeError("critique must be Critique")
    # 第二轮不再注入失败；weak_step_id 仅作可观测信号
    _ = critique.weak_step_id or trace.stop_reason
    return execute_plan(plan, fail_step_id=None)


def _transition(state: str, event: str) -> str:
    """最小转移表。"""
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
    """编排完整研究任务，返回可展示结果。"""
    if not isinstance(max_rounds, int) or isinstance(max_rounds, bool) or max_rounds < 1:
        raise ValueError("max_rounds must be int >= 1")

    state = STATE_IDLE
    path = [STATE_IDLE]
    critiques: list[Critique] = []

    state = _transition(state, EVENT_GOAL_RECEIVED)
    path.append(state)
    plan = build_research_plan(goal, max_steps=max_steps)

    state = _transition(state, EVENT_PLAN_READY)
    path.append(state)

    trace: ExecutionTrace | None = None
    final_decision = DECISION_ABORT
    rounds = 0

    for round_index in range(1, max_rounds + 1):
        rounds = round_index
        if state != STATE_EXECUTING:
            state = _transition(state, EVENT_DECISION_RETRY)
            path.append(state)

        if round_index == 1:
            trace = execute_plan(plan, fail_step_id=inject_fail_step)
        else:
            assert trace is not None
            # 上一轮 critique 已在列表末尾
            trace = apply_retry(plan, trace, critiques[-1])

        state = _transition(state, EVENT_EXECUTION_FINISHED)
        path.append(state)

        critique = critique_trace(trace)
        critiques.append(critique)

        if critique.decision == DECISION_ACCEPT:
            state = _transition(state, EVENT_DECISION_ACCEPT)
            path.append(state)
            final_decision = DECISION_ACCEPT
            break

        if critique.decision == DECISION_RETRY:
            if round_index >= max_rounds:
                state = _transition(state, EVENT_DECISION_ABORT)
                path.append(state)
                final_decision = DECISION_ABORT
                break
            # 下一轮循环开头会 decision_retry → executing
            continue

        # abort（今日 critique 不会主动给，但管线需容忍）
        state = _transition(state, EVENT_DECISION_ABORT)
        path.append(state)
        final_decision = DECISION_ABORT
        break
    else:
        # 理论上由 break 退出；兜底
        if state == STATE_REFLECTING:
            state = _transition(state, EVENT_DECISION_ABORT)
            path.append(state)
        final_decision = DECISION_ABORT

    assert trace is not None
    return ResearchRun(
        goal=plan.goal,
        plan=plan,
        trace=trace,
        decision=final_decision,
        state_path=path,
        rounds=rounds,
        critiques=critiques,
    )


def render_plan(plan: Plan) -> str:
    """把计划渲染成 Markdown。"""
    if not isinstance(plan, Plan):
        raise TypeError("plan must be Plan")
    lines = [
        f"# 研究计划｜{plan.goal}",
        "",
        f"- 策略：`{plan.strategy}`",
        f"- 步数：{len(plan.steps)}",
        "",
        "| ID | Kind | Title | Depends |",
        "|----|------|-------|---------|",
    ]
    for s in plan.steps:
        deps = ", ".join(s.depends_on) if s.depends_on else "—"
        lines.append(f"| `{s.id}` | `{s.kind}` | {s.title} | {deps} |")
    lines.append("")
    for s in plan.steps:
        lines.append(f"### `{s.id}` {s.title}")
        lines.append("")
        lines.append(s.detail)
        lines.append("")
    return "\n".join(lines)


def render_execution(trace: ExecutionTrace) -> str:
    """把执行轨迹渲染成 Markdown 表格。"""
    if not isinstance(trace, ExecutionTrace):
        raise TypeError("trace must be ExecutionTrace")
    lines = [
        f"# 执行轨迹｜{trace.goal}",
        "",
        f"- stop_reason：`{trace.stop_reason}`",
        f"- deliverable：{'有' if trace.deliverable.strip() else '无'}",
        "",
        "| Step | Status | Tool | Observation / Error |",
        "|------|--------|------|---------------------|",
    ]
    for r in trace.results:
        detail = r.observation if r.status == STATUS_DONE else (r.error or "—")
        detail = detail.replace("|", "\\|").replace("\n", " ")
        if len(detail) > 80:
            detail = detail[:77] + "..."
        lines.append(
            f"| `{r.step_id}` | `{r.status}` | `{r.tool_name}` | {detail} |"
        )
    lines.append("")
    if trace.deliverable.strip():
        lines.append("## Deliverable")
        lines.append("")
        lines.append("```text")
        lines.append(trace.deliverable.rstrip())
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def summarize_run(run: ResearchRun) -> dict[str, object]:
    """汇总单次运行。"""
    if not isinstance(run, ResearchRun):
        raise TypeError("run must be ResearchRun")
    return {
        "goal": run.goal,
        "decision": run.decision,
        "rounds": run.rounds,
        "steps": len(run.plan.steps),
        "stop_reason": run.trace.stop_reason,
        "has_deliverable": bool(run.trace.deliverable.strip()),
        "state_path": list(run.state_path),
    }


def build_demo_runs() -> list[ResearchRun]:
    """至少 2 条：happy path + 注入失败后 retry 成功。"""
    happy = run_research_task("调研向量数据库选型")
    retry = run_research_task(
        "对比开源向量库与托管方案",
        inject_fail_step="S2",
        max_rounds=2,
    )
    return [happy, retry]


def render_research_report(runs: Sequence[ResearchRun] | None = None) -> str:
    """生成含固定二级标题的学习报告。"""
    items = list(runs) if runs is not None else build_demo_runs()
    if not items:
        items = build_demo_runs()
    summaries = [summarize_run(r) for r in items]
    accepted = sum(1 for s in summaries if s["decision"] == DECISION_ACCEPT)
    aborted = sum(1 for s in summaries if s["decision"] == DECISION_ABORT)
    sample = items[0]

    lines = [
        "# Day 70 报告｜周挑战：多步研究任务",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[0]}",
        "",
        "多步研究任务 = **可见计划** + **逐步执行** + **反思纠错** + **状态回放**。",
        "观众先看到「打算做什么」，再看到「每步观察到什么」，最后看到交付摘要。",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[1]}",
        "",
        "- Day 66 Planner → `build_research_plan`",
        "- Day 67 Executor → `execute_plan`",
        "- Day 68 Reflection → `critique_trace` / `apply_retry`",
        "- Day 69 FSM → `_transition` 累积 `state_path`",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[2]}",
        "",
        "### 样例计划",
        "",
        render_plan(sample.plan),
        "### 样例执行",
        "",
        render_execution(sample.trace),
        f"状态路径：`{' → '.join(sample.state_path)}`",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[3]}",
        "",
        f"- 演示次数：{len(summaries)}",
        f"- accept：{accepted} · abort：{aborted}",
        f"- 样例轮次：{sample.rounds} · 最终决策：`{sample.decision}`",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[4]}",
        "",
        "Day 71｜何时需要 Multi-Agent——单管线不够时，再拆 Researcher / Writer。",
        "",
    ]
    return "\n".join(lines)
