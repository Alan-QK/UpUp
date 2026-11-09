"""Day 67 参考实现：Plan-and-Execute 执行器。

吃进 Day 66 的 Plan，按 depends_on 逐步调用工具，把观察写回共享黑板。
全程标准库，不调用 LLM——工具用确定性 mock，方便单测。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Sequence

# --- Plan 模型（与 Day 66 对齐，今日只读不改） ---

GOAL_KIND_RESEARCH = "research"
GOAL_KIND_CODING = "coding"
GOAL_KIND_WRITING = "writing"
GOAL_KIND_OPS = "ops"
GOAL_KIND_GENERIC = "generic"
VALID_GOAL_KINDS = frozenset(
    {
        GOAL_KIND_RESEARCH,
        GOAL_KIND_CODING,
        GOAL_KIND_WRITING,
        GOAL_KIND_OPS,
        GOAL_KIND_GENERIC,
    }
)

STEP_KIND_CLARIFY = "clarify"
STEP_KIND_RESEARCH = "research"
STEP_KIND_DESIGN = "design"
STEP_KIND_EXECUTE = "execute"
STEP_KIND_ANALYZE = "analyze"
STEP_KIND_VERIFY = "verify"
STEP_KIND_DELIVER = "deliver"
VALID_STEP_KINDS = frozenset(
    {
        STEP_KIND_CLARIFY,
        STEP_KIND_RESEARCH,
        STEP_KIND_DESIGN,
        STEP_KIND_EXECUTE,
        STEP_KIND_ANALYZE,
        STEP_KIND_VERIFY,
        STEP_KIND_DELIVER,
    }
)

COMPLEXITY_SIMPLE = "simple"
COMPLEXITY_MEDIUM = "medium"
COMPLEXITY_COMPLEX = "complex"
VALID_COMPLEXITIES = frozenset(
    {COMPLEXITY_SIMPLE, COMPLEXITY_MEDIUM, COMPLEXITY_COMPLEX}
)

# --- 执行状态 ---

STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"
VALID_STATUSES = frozenset(
    {
        STATUS_PENDING,
        STATUS_RUNNING,
        STATUS_DONE,
        STATUS_FAILED,
        STATUS_SKIPPED,
    }
)

STOP_COMPLETED = "completed"
STOP_FAILED = "failed"
STOP_BLOCKED = "blocked"
STOP_MAX_STEPS = "max_steps"
VALID_STOP_REASONS = frozenset(
    {STOP_COMPLETED, STOP_FAILED, STOP_BLOCKED, STOP_MAX_STEPS}
)

# step.kind → 工具名（可观测、可替换）
KIND_TO_TOOL: dict[str, str] = {
    STEP_KIND_CLARIFY: "clarify_goal",
    STEP_KIND_RESEARCH: "search_notes",
    STEP_KIND_DESIGN: "draft_outline",
    STEP_KIND_EXECUTE: "run_action",
    STEP_KIND_ANALYZE: "analyze_findings",
    STEP_KIND_VERIFY: "verify_checklist",
    STEP_KIND_DELIVER: "write_deliverable",
}

REQUIRED_TOOLS = frozenset(KIND_TO_TOOL.values())

REQUIRED_REPORT_SECTIONS = (
    "何为 Plan-and-Execute",
    "依赖与工具映射",
    "今日演示统计",
    "与 Reflection 衔接",
    "明日预告",
)

ToolHandler = Callable[["PlanStep", dict[str, object]], str]


@dataclass(frozen=True)
class PlanStep:
    """计划中的一步（只读）。"""

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
        for dep in self.depends_on:
            if not isinstance(dep, str) or not dep.strip():
                raise ValueError("depends_on entries must be non-empty str")


@dataclass(frozen=True)
class Plan:
    """一份可执行的计划。"""

    goal: str
    steps: tuple[PlanStep, ...]
    goal_kind: str
    strategy: str
    complexity: str

    def __post_init__(self) -> None:
        if not isinstance(self.goal, str) or not self.goal.strip():
            raise ValueError("goal must be non-empty str")
        if not isinstance(self.steps, tuple) or not self.steps:
            raise ValueError("steps must be non-empty tuple")
        if self.goal_kind not in VALID_GOAL_KINDS:
            raise ValueError(f"invalid goal_kind: {self.goal_kind}")
        if not isinstance(self.strategy, str) or not self.strategy.strip():
            raise ValueError("strategy must be non-empty str")
        if self.complexity not in VALID_COMPLEXITIES:
            raise ValueError(f"invalid complexity: {self.complexity}")
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
class ToolSpec:
    """可注册的工具。"""

    name: str
    description: str
    handler: ToolHandler

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("tool name must be non-empty str")
        if not isinstance(self.description, str):
            raise TypeError("description must be str")
        if not callable(self.handler):
            raise TypeError("handler must be callable")


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
class ExecutionState:
    """一次计划执行的共享状态（黑板）。"""

    plan: Plan
    results: dict[str, StepResult] = field(default_factory=dict)
    context: dict[str, object] = field(default_factory=dict)
    stop_reason: str = STOP_COMPLETED
    steps_run: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.plan, Plan):
            raise TypeError("plan must be Plan")
        if self.stop_reason not in VALID_STOP_REASONS:
            raise ValueError(f"invalid stop_reason: {self.stop_reason}")


# --- mock 工具（确定性，读/写 context） ---


def _tool_clarify_goal(step: PlanStep, context: dict[str, object]) -> str:
    goal = str(context.get("goal", ""))
    scope = f"已澄清目标：「{goal}」。范围：{step.detail}"
    context["clarified"] = scope
    context["notes"] = list(context.get("notes", []))  # type: ignore[arg-type]
    return scope


def _tool_search_notes(step: PlanStep, context: dict[str, object]) -> str:
    goal = str(context.get("goal", ""))
    hits = [
        f"笔记#1：关于「{goal}」的背景摘要",
        f"笔记#2：与「{step.title}」相关的要点",
    ]
    notes = list(context.get("notes", []))  # type: ignore[arg-type]
    notes.extend(hits)
    context["notes"] = notes
    context["last_search"] = hits
    return "；".join(hits)


def _tool_draft_outline(step: PlanStep, context: dict[str, object]) -> str:
    outline = [
        "1. 背景",
        "2. 方案对比",
        f"3. 执行：{step.title}",
        "4. 验收",
    ]
    context["outline"] = outline
    return "大纲 → " + " / ".join(outline)


def _tool_run_action(step: PlanStep, context: dict[str, object]) -> str:
    actions = list(context.get("actions", []))  # type: ignore[arg-type]
    msg = f"已执行：{step.title}（{step.detail}）"
    actions.append(msg)
    context["actions"] = actions
    return msg


def _tool_analyze_findings(step: PlanStep, context: dict[str, object]) -> str:
    notes = list(context.get("notes", []))  # type: ignore[arg-type]
    n = len(notes)
    summary = f"分析完成：基于 {n} 条笔记，聚焦「{step.title}」。"
    context["analysis"] = summary
    return summary


def _tool_verify_checklist(step: PlanStep, context: dict[str, object]) -> str:
    checks = [
        "主路径可复现",
        "依赖步骤均已 DONE",
        f"核对：{step.title}",
    ]
    context["checklist"] = checks
    return "验收通过 → " + "；".join(checks)


def _tool_write_deliverable(step: PlanStep, context: dict[str, object]) -> str:
    goal = str(context.get("goal", ""))
    body = (
        f"# 交付物：{goal}\n"
        f"- 澄清：{context.get('clarified', '（无）')}\n"
        f"- 分析：{context.get('analysis', '（无）')}\n"
        f"- 步骤：{step.title}\n"
    )
    context["deliverable"] = body
    return f"已写入交付物（{len(body)} 字符）"


def _tool_boom(_step: PlanStep, _context: dict[str, object]) -> str:
    """测试用：故意失败。"""
    raise RuntimeError("simulated tool failure")


def default_tool_registry(*, include_boom: bool = False) -> dict[str, ToolSpec]:
    """返回默认工具表；可选附带 boom 失败工具。"""
    specs = [
        ToolSpec("clarify_goal", "澄清目标与范围", _tool_clarify_goal),
        ToolSpec("search_notes", "检索本地笔记（mock）", _tool_search_notes),
        ToolSpec("draft_outline", "起草大纲", _tool_draft_outline),
        ToolSpec("run_action", "执行主路径动作", _tool_run_action),
        ToolSpec("analyze_findings", "分析已收集材料", _tool_analyze_findings),
        ToolSpec("verify_checklist", "验收检查清单", _tool_verify_checklist),
        ToolSpec("write_deliverable", "写出交付物", _tool_write_deliverable),
    ]
    registry = {s.name: s for s in specs}
    if include_boom:
        registry["boom"] = ToolSpec("boom", "故意失败", _tool_boom)
    missing = REQUIRED_TOOLS - set(registry)
    if missing:
        raise ValueError(f"registry missing tools: {sorted(missing)}")
    return registry


def kind_to_tool_name(kind: str) -> str:
    """把 step.kind 映射到工具名。"""
    if kind not in VALID_STEP_KINDS:
        raise ValueError(f"invalid step kind: {kind}")
    return KIND_TO_TOOL[kind]


def deps_satisfied(step: PlanStep, results: dict[str, StepResult]) -> bool:
    """所有 depends_on 是否均为 DONE。"""
    for dep in step.depends_on:
        r = results.get(dep)
        if r is None or r.status != STATUS_DONE:
            return False
    return True


def invoke_tool(
    tool_name: str,
    step: PlanStep,
    context: dict[str, object],
    registry: dict[str, ToolSpec],
) -> str:
    """调用工具；未知工具抛 KeyError；handler 异常向上抛。"""
    if tool_name not in registry:
        raise KeyError(f"unknown tool: {tool_name}")
    spec = registry[tool_name]
    obs = spec.handler(step, context)
    if not isinstance(obs, str):
        raise TypeError("tool handler must return str")
    return obs


def _pending_or_blocked(
    step: PlanStep,
    results: dict[str, StepResult],
) -> StepResult | None:
    """若依赖未满足，返回 SKIPPED 结果；否则 None。"""
    if deps_satisfied(step, results):
        return None
    tool = kind_to_tool_name(step.kind)
    return StepResult(
        step_id=step.id,
        status=STATUS_SKIPPED,
        tool_name=tool,
        observation="",
        error="dependencies not satisfied",
    )


def execute_plan(
    plan: Plan,
    *,
    registry: dict[str, ToolSpec] | None = None,
    stop_on_failure: bool = True,
    max_steps: int | None = None,
    kind_overrides: dict[str, str] | None = None,
) -> ExecutionState:
    """按计划顺序执行步骤。

    规则：
    1. 初始化 context['goal']=plan.goal
    2. 按 plan.steps 顺序遍历（今日不做并行调度）
    3. 依赖未 DONE → SKIPPED；若 stop_on_failure 则 stop_reason=blocked
    4. 否则映射工具并调用；成功 → DONE；异常 → FAILED
    5. stop_on_failure 时遇到 FAILED/BLOCKED 立即停，后续标 SKIPPED
    6. max_steps 限制「实际调用工具」的次数（不含 skip）
    """
    if not isinstance(plan, Plan):
        raise TypeError("plan must be Plan")
    if max_steps is not None:
        if not isinstance(max_steps, int) or isinstance(max_steps, bool):
            raise TypeError("max_steps must be int or None")
        if max_steps < 1:
            raise ValueError("max_steps must be >= 1")

    reg = registry if registry is not None else default_tool_registry()
    overrides = kind_overrides or {}
    state = ExecutionState(plan=plan)
    state.context["goal"] = plan.goal
    state.context["notes"] = []
    state.context["actions"] = []

    remaining_after_stop: list[PlanStep] = []
    stopped = False

    for step in plan.steps:
        if stopped:
            remaining_after_stop.append(step)
            continue

        if max_steps is not None and state.steps_run >= max_steps:
            state.stop_reason = STOP_MAX_STEPS
            remaining_after_stop.append(step)
            stopped = True
            continue

        blocked = _pending_or_blocked(step, state.results)
        if blocked is not None:
            state.results[step.id] = blocked
            if stop_on_failure:
                state.stop_reason = STOP_BLOCKED
                stopped = True
            continue

        tool_name = overrides.get(step.kind) or kind_to_tool_name(step.kind)
        try:
            obs = invoke_tool(tool_name, step, state.context, reg)
            state.results[step.id] = StepResult(
                step_id=step.id,
                status=STATUS_DONE,
                tool_name=tool_name,
                observation=obs,
            )
            state.steps_run += 1
        except Exception as exc:  # noqa: BLE001 — 执行器要吞并记录
            state.results[step.id] = StepResult(
                step_id=step.id,
                status=STATUS_FAILED,
                tool_name=tool_name,
                observation="",
                error=f"{type(exc).__name__}: {exc}",
            )
            state.steps_run += 1
            if stop_on_failure:
                state.stop_reason = STOP_FAILED
                stopped = True

    for step in remaining_after_stop:
        if step.id in state.results:
            continue
        tool_name = overrides.get(step.kind) or kind_to_tool_name(step.kind)
        state.results[step.id] = StepResult(
            step_id=step.id,
            status=STATUS_SKIPPED,
            tool_name=tool_name,
            error="stopped before reach",
        )

    if not stopped and state.stop_reason not in {
        STOP_FAILED,
        STOP_BLOCKED,
        STOP_MAX_STEPS,
    }:
        # 若有任何 FAILED 且未提前停（stop_on_failure=False）
        if any(r.status == STATUS_FAILED for r in state.results.values()):
            state.stop_reason = STOP_FAILED
        elif any(r.status == STATUS_SKIPPED for r in state.results.values()):
            # 有 skip 但跑完了（例如 stop_on_failure=False 且依赖失败）
            if any(r.status == STATUS_DONE for r in state.results.values()):
                state.stop_reason = STOP_COMPLETED
            else:
                state.stop_reason = STOP_BLOCKED
        else:
            state.stop_reason = STOP_COMPLETED

    return state


def summarize_execution(state: ExecutionState) -> dict[str, object]:
    """汇总执行结果。"""
    by_status: dict[str, int] = {}
    for r in state.results.values():
        by_status[r.status] = by_status.get(r.status, 0) + 1
    return {
        "goal": state.plan.goal,
        "stop_reason": state.stop_reason,
        "steps_run": state.steps_run,
        "total_steps": len(state.plan.steps),
        "by_status": by_status,
        "has_deliverable": "deliverable" in state.context,
    }


def render_execution(state: ExecutionState) -> str:
    """把执行轨迹渲染成 Markdown。"""
    if not isinstance(state, ExecutionState):
        raise TypeError("state must be ExecutionState")
    lines = [
        f"# 执行轨迹：{state.plan.goal}",
        "",
        f"- 停止原因：`{state.stop_reason}`",
        f"- 实际调用：{state.steps_run} / {len(state.plan.steps)}",
        f"- 策略：`{state.plan.strategy}`",
        "",
        "## 步骤结果",
        "",
    ]
    for step in state.plan.steps:
        r = state.results.get(step.id)
        if r is None:
            lines.append(f"### {step.id}. {step.title}")
            lines.append("- 状态：`missing`")
            lines.append("")
            continue
        lines.append(f"### {step.id}. {step.title}")
        lines.append(f"- 状态：`{r.status}`")
        lines.append(f"- 工具：`{r.tool_name}`")
        if r.observation:
            lines.append(f"- 观察：{r.observation}")
        if r.error:
            lines.append(f"- 错误：{r.error}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_sample_plan(
    *,
    goal: str = "调研向量数据库选型",
    goal_kind: str = GOAL_KIND_RESEARCH,
    with_deliver: bool = True,
) -> Plan:
    """构造一份可演示的串行计划（不依赖 Day66 模块）。"""
    raw: list[tuple[str, str, str]] = [
        ("澄清调研范围", "明确核心问题与受众。", STEP_KIND_CLARIFY),
        ("收集资料", "检索笔记与权威来源。", STEP_KIND_RESEARCH),
        ("交叉比对", "整理异同与适用场景。", STEP_KIND_ANALYZE),
    ]
    if with_deliver:
        raw.append(("形成结论", "输出简短推荐。", STEP_KIND_DELIVER))
    steps: list[PlanStep] = []
    for i, (title, detail, kind) in enumerate(raw, start=1):
        sid = f"S{i}"
        deps: tuple[str, ...] = (f"S{i - 1}",) if i > 1 else ()
        steps.append(
            PlanStep(
                id=sid,
                title=title,
                detail=detail,
                kind=kind,
                depends_on=deps,
            )
        )
    return Plan(
        goal=goal,
        steps=tuple(steps),
        goal_kind=goal_kind,
        strategy=f"heuristic:{goal_kind}",
        complexity=COMPLEXITY_MEDIUM,
    )


def build_demo_plans() -> list[Plan]:
    """演示用多份计划。"""
    return [
        build_sample_plan(goal="调研向量数据库选型", goal_kind=GOAL_KIND_RESEARCH),
        build_sample_plan(
            goal="实现带重试的 HTTP 客户端",
            goal_kind=GOAL_KIND_CODING,
        ),
        build_sample_plan(
            goal="写一份记忆系统设计文档",
            goal_kind=GOAL_KIND_WRITING,
            with_deliver=True,
        ),
    ]


def run_demo_executor(plans: Sequence[Plan] | None = None) -> list[ExecutionState]:
    """批量执行演示计划。"""
    items = list(plans) if plans is not None else build_demo_plans()
    reg = default_tool_registry()
    return [execute_plan(p, registry=reg) for p in items]


def render_executor_report(states: Sequence[ExecutionState] | None = None) -> str:
    """生成含固定二级标题的学习报告。"""
    if states is None:
        states = run_demo_executor()
    done = sum(
        1 for s in states if s.stop_reason == STOP_COMPLETED
    )
    total_run = sum(s.steps_run for s in states)
    sample = states[0] if states else None
    sample_md = render_execution(sample) if sample else "_（无执行结果）_"
    stats_lines = [
        f"- 计划数：{len(states)}",
        f"- 完整完成：{done}",
        f"- 累计工具调用：{total_run}",
    ]
    if sample:
        sm = summarize_execution(sample)
        stats_lines.append(f"- 样例 by_status：{sm['by_status']}")

    lines = [
        "# Day 67 报告｜Plan-and-Execute",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[0]}",
        "",
        "Plan-and-Execute = **先拿到结构化 Plan，再按依赖逐步调工具**。",
        "与「一口气让模型边想边做」相比，步骤可暂停、可重试、可观测。",
        "今日执行器用 mock 工具，结构与生产一致。",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[1]}",
        "",
        "依赖：`depends_on` 必须全部 `done` 才可执行；否则 `skipped`。",
        "映射：`clarify→clarify_goal`，`research→search_notes`，",
        "`design→draft_outline`，`execute→run_action`，",
        "`analyze→analyze_findings`，`verify→verify_checklist`，",
        "`deliver→write_deliverable`。",
        "共享 `context` 充当黑板：上一步观察可供下一步读取。",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[2]}",
        "",
        *stats_lines,
        "",
        "### 样例轨迹",
        "",
        sample_md,
        f"## {REQUIRED_REPORT_SECTIONS[3]}",
        "",
        "明日 Day 68 会加 Reflection：对失败/低质量观察做 critic，",
        "决定重试、改计划或接受结果——执行器提供轨迹，反思器负责纠错。",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[4]}",
        "",
        "Day 68｜Reflection 反思纠错：增加 critic 轮。",
        "",
    ]
    return "\n".join(lines)
