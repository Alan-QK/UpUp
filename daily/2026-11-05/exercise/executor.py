"""Day 67 练习：Plan-and-Execute 执行器。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——不调用 LLM。

提示：
- Plan / PlanStep 已给齐（与 Day 66 对齐），今日只读
- 先实现 kind_to_tool_name / deps_satisfied / default_tool_registry
- 再实现 invoke_tool / execute_plan
- 最后做 render / demo / report
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

# step.kind → 工具名（已给齐，勿改键值）
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


# --- mock 工具骨架（可直接复用；需写入 context） ---


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
    """返回默认工具表；必须覆盖 REQUIRED_TOOLS。

    include_boom=True 时额外注册 name=boom 的失败工具。
    """
    # TODO
    raise NotImplementedError


def kind_to_tool_name(kind: str) -> str:
    """把 step.kind 映射到工具名；非法 kind 抛 ValueError。"""
    # TODO: 查 KIND_TO_TOOL
    raise NotImplementedError


def deps_satisfied(step: PlanStep, results: dict[str, StepResult]) -> bool:
    """所有 depends_on 是否均为 STATUS_DONE。"""
    # TODO
    raise NotImplementedError


def invoke_tool(
    tool_name: str,
    step: PlanStep,
    context: dict[str, object],
    registry: dict[str, ToolSpec],
) -> str:
    """调用工具。

    - 未知工具：KeyError
    - handler 必须返回 str，否则 TypeError
    - handler 内异常不要在这里吞掉（交给 execute_plan）
    """
    # TODO
    raise NotImplementedError


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
    1. 校验 plan；max_steps 若给则须为 >=1 的 int（拒绝 bool）
    2. registry 默认 default_tool_registry()
    3. context 初始化 goal/notes/actions
    4. 按 steps 顺序：
       - 若已 stop：后续全部 SKIPPED（error=stopped before reach）
       - 若 steps_run >= max_steps：stop_reason=max_steps，当前及后续 SKIPPED
       - 依赖未满足：SKIPPED（error=dependencies not satisfied）；
         stop_on_failure 时 stop_reason=blocked 并停止
       - 否则取工具（kind_overrides 优先）并 invoke：
         成功 → DONE 且 steps_run+=1
         异常 → FAILED，记录 error；stop_on_failure 时 stop_reason=failed
    5. 若未中途停止：全 DONE → completed；有 FAILED → failed
    """
    # TODO
    raise NotImplementedError


def summarize_execution(state: ExecutionState) -> dict[str, object]:
    """返回 goal / stop_reason / steps_run / total_steps / by_status / has_deliverable。"""
    # TODO
    raise NotImplementedError


def render_execution(state: ExecutionState) -> str:
    """把执行轨迹渲染成 Markdown（含停止原因与每步状态）。"""
    # TODO
    raise NotImplementedError


def build_sample_plan(
    *,
    goal: str = "调研向量数据库选型",
    goal_kind: str = GOAL_KIND_RESEARCH,
    with_deliver: bool = True,
) -> Plan:
    """构造一份串行演示计划（clarify→research→analyze[→deliver]）。"""
    # TODO: S1 无依赖，Si 依赖 S(i-1)；strategy=heuristic:<kind>
    raise NotImplementedError


def build_demo_plans() -> list[Plan]:
    """返回至少 3 份不同 goal_kind 的演示计划。"""
    # TODO
    raise NotImplementedError


def run_demo_executor(plans: Sequence[Plan] | None = None) -> list[ExecutionState]:
    """批量执行；默认 build_demo_plans()。"""
    # TODO
    raise NotImplementedError


def render_executor_report(states: Sequence[ExecutionState] | None = None) -> str:
    """生成报告；必须包含 REQUIRED_REPORT_SECTIONS 中每个标题（作 ## 二级标题）。"""
    # TODO
    raise NotImplementedError
