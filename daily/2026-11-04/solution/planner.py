"""Day 66 参考实现：任务分解 Planner（目标 → 步骤列表）。

全程标准库。不调用 LLM——用可复现的启发式模板拆目标。
生产环境可把 `plan_from_goal` 换成 LLM，但 Plan / PlanStep 结构保持不变。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

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

MIN_GOAL_LEN = 4
DEFAULT_MAX_STEPS = 8
MIN_MAX_STEPS = 3
MAX_MAX_STEPS = 12

REQUIRED_REPORT_SECTIONS = (
    "何为任务分解 Planner",
    "目标分类与模板",
    "今日演示统计",
    "与 Plan-and-Execute 衔接",
    "明日预告",
)

_RESEARCH_RE = re.compile(
    r"(调研|研究|对比|比较|查一下|分析一下|评估|investigate|research|compare)",
    re.IGNORECASE,
)
_CODING_RE = re.compile(
    r"(实现|开发|写一个|写个|修复|重构|refactor|implement|bug|代码|函数|模块|api)",
    re.IGNORECASE,
)
_WRITING_RE = re.compile(
    r"(写文档|写报告|写总结|撰写|博客|readme|文档|文案|draft|write\s+(a|an|the)\s)",
    re.IGNORECASE,
)
_OPS_RE = re.compile(
    r"(部署|发布|上线|回滚|监控|运维|deploy|release|rollback|monitor)",
    re.IGNORECASE,
)
_COMPLEX_HINT_RE = re.compile(
    r"(并且|同时|然后|之后|以及|再|完整|端到端|全流程|多步骤|and\s+then)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PlanStep:
    """计划中的一步。"""

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
    """一份可展示、可后续交给执行器的计划。"""

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


def normalize_goal(text: str) -> str:
    """去掉首尾空白、压缩中间空白。"""
    if not isinstance(text, str):
        raise TypeError("goal must be str")
    return re.sub(r"\s+", " ", text).strip()


def classify_goal(goal: str) -> str:
    """按关键词启发式分类目标（可被 LLM 分类器替换）。"""
    g = normalize_goal(goal)
    if len(g) < MIN_GOAL_LEN:
        raise ValueError(f"goal too short: need >= {MIN_GOAL_LEN} chars")
    # 顺序：更具体的意图优先
    if _CODING_RE.search(g):
        return GOAL_KIND_CODING
    if _WRITING_RE.search(g):
        return GOAL_KIND_WRITING
    if _OPS_RE.search(g):
        return GOAL_KIND_OPS
    if _RESEARCH_RE.search(g):
        return GOAL_KIND_RESEARCH
    return GOAL_KIND_GENERIC


def estimate_complexity(goal: str, step_count: int) -> str:
    """根据目标措辞与步数估复杂度。"""
    g = normalize_goal(goal)
    hints = len(_COMPLEX_HINT_RE.findall(g))
    if step_count <= 3 and hints == 0 and len(g) < 24:
        return COMPLEXITY_SIMPLE
    if step_count >= 7 or hints >= 2 or len(g) > 80:
        return COMPLEXITY_COMPLEX
    return COMPLEXITY_MEDIUM


def _clamp_max_steps(max_steps: int) -> int:
    if not isinstance(max_steps, int) or isinstance(max_steps, bool):
        raise TypeError("max_steps must be int")
    if max_steps < MIN_MAX_STEPS or max_steps > MAX_MAX_STEPS:
        raise ValueError(
            f"max_steps must be in [{MIN_MAX_STEPS}, {MAX_MAX_STEPS}]"
        )
    return max_steps


def _templates(goal: str, kind: str) -> list[tuple[str, str, str]]:
    """返回 (title, detail, step_kind) 模板列表（未裁剪）。"""
    if kind == GOAL_KIND_RESEARCH:
        return [
            (
                "澄清调研范围",
                f"明确「{goal}」要回答的核心问题、受众与成功标准。",
                STEP_KIND_CLARIFY,
            ),
            (
                "收集资料",
                "检索官方文档、权威文章与对比材料，记录来源。",
                STEP_KIND_RESEARCH,
            ),
            (
                "交叉比对",
                "整理异同点、可信度与适用场景。",
                STEP_KIND_ANALYZE,
            ),
            (
                "形成结论",
                "输出简短结论与推荐，并标注不确定处。",
                STEP_KIND_DELIVER,
            ),
            (
                "核对遗漏",
                "对照初始问题检查是否回答完整。",
                STEP_KIND_VERIFY,
            ),
        ]
    if kind == GOAL_KIND_CODING:
        return [
            (
                "澄清需求与验收",
                f"把「{goal}」拆成可测的输入/输出与边界条件。",
                STEP_KIND_CLARIFY,
            ),
            (
                "设计接口与结构",
                "确定模块边界、数据结构与错误约定。",
                STEP_KIND_DESIGN,
            ),
            (
                "实现核心逻辑",
                "先打通主路径，再补边界分支。",
                STEP_KIND_EXECUTE,
            ),
            (
                "编写/补齐测试",
                "用最小用例覆盖主路径与关键失败路径。",
                STEP_KIND_VERIFY,
            ),
            (
                "自审与整理",
                "检查命名、日志与 README 使用说明。",
                STEP_KIND_DELIVER,
            ),
        ]
    if kind == GOAL_KIND_WRITING:
        return [
            (
                "明确读者与目的",
                f"确认「{goal}」的读者、篇幅与语气。",
                STEP_KIND_CLARIFY,
            ),
            (
                "列出大纲",
                "用 3–7 个二级标题框住结构。",
                STEP_KIND_DESIGN,
            ),
            (
                "起草正文",
                "按大纲填充，先求完整再求文采。",
                STEP_KIND_EXECUTE,
            ),
            (
                "修订润色",
                "删冗余、统一术语、补例子。",
                STEP_KIND_ANALYZE,
            ),
            (
                "终检交付",
                "检查标题层级、链接与结论是否可扫读。",
                STEP_KIND_DELIVER,
            ),
        ]
    if kind == GOAL_KIND_OPS:
        return [
            (
                "确认变更范围",
                f"列出「{goal}」涉及的服务、环境与回滚点。",
                STEP_KIND_CLARIFY,
            ),
            (
                "准备清单与检查",
                "核对配置、权限、依赖与监控面板。",
                STEP_KIND_DESIGN,
            ),
            (
                "执行变更",
                "按清单逐步操作，记录每步结果。",
                STEP_KIND_EXECUTE,
            ),
            (
                "验证健康状态",
                "检查指标、日志与关键路径冒烟。",
                STEP_KIND_VERIFY,
            ),
            (
                "通报结果",
                "同步成功/回滚状态与后续观察项。",
                STEP_KIND_DELIVER,
            ),
        ]
    # generic
    return [
        (
            "澄清目标",
            f"用一句话重述「{goal}」，并写出完成定义。",
            STEP_KIND_CLARIFY,
        ),
        (
            "拆成可执行块",
            "找出依赖顺序，避免一口气做太大块。",
            STEP_KIND_DESIGN,
        ),
        (
            "执行主路径",
            "先完成能验证进度的最小一步。",
            STEP_KIND_EXECUTE,
        ),
        (
            "检查结果",
            "对照完成定义验收，记录缺口。",
            STEP_KIND_VERIFY,
        ),
        (
            "交付与复盘",
            "整理产出，记下下次可改进点。",
            STEP_KIND_DELIVER,
        ),
    ]


def _build_steps(
    templates: Sequence[tuple[str, str, str]],
    max_steps: int,
) -> tuple[PlanStep, ...]:
    chosen = list(templates[:max_steps])
    if len(chosen) < MIN_MAX_STEPS:
        # 模板本身不会短于 3；防御性填充
        while len(chosen) < MIN_MAX_STEPS:
            idx = len(chosen) + 1
            chosen.append(
                (
                    f"补充步骤 {idx}",
                    "完善尚未覆盖的子任务。",
                    STEP_KIND_EXECUTE,
                )
            )
    steps: list[PlanStep] = []
    for i, (title, detail, kind) in enumerate(chosen, start=1):
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
    return tuple(steps)


def plan_from_goal(goal: str, *, max_steps: int = DEFAULT_MAX_STEPS) -> Plan:
    """把自然语言目标拆成有序步骤列表。"""
    max_steps = _clamp_max_steps(max_steps)
    normalized = normalize_goal(goal)
    if len(normalized) < MIN_GOAL_LEN:
        raise ValueError(f"goal too short: need >= {MIN_GOAL_LEN} chars")
    kind = classify_goal(normalized)
    templates = _templates(normalized, kind)
    # 简单目标可少几步：无复杂提示且短句 → 最多 3 步
    effective_max = max_steps
    if (
        len(normalized) < 20
        and not _COMPLEX_HINT_RE.search(normalized)
        and max_steps > 3
    ):
        effective_max = 3
    steps = _build_steps(templates, effective_max)
    complexity = estimate_complexity(normalized, len(steps))
    strategy = f"heuristic:{kind}"
    return Plan(
        goal=normalized,
        steps=steps,
        goal_kind=kind,
        strategy=strategy,
        complexity=complexity,
    )


def render_plan(plan: Plan) -> str:
    """把计划渲染成便于人读的 Markdown。"""
    if not isinstance(plan, Plan):
        raise TypeError("plan must be Plan")
    lines = [
        f"# 计划：{plan.goal}",
        "",
        f"- 分类：`{plan.goal_kind}`",
        f"- 策略：`{plan.strategy}`",
        f"- 复杂度：`{plan.complexity}`",
        f"- 步数：{len(plan.steps)}",
        "",
        "## 步骤",
        "",
    ]
    for step in plan.steps:
        deps = ", ".join(step.depends_on) if step.depends_on else "—"
        lines.append(f"### {step.id}. {step.title}")
        lines.append(f"- 类型：`{step.kind}`")
        lines.append(f"- 依赖：{deps}")
        lines.append(f"- 说明：{step.detail}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_demo_goals() -> list[str]:
    """演示用目标集合。"""
    return [
        "调研 LangGraph 与自研状态机的取舍",
        "实现一个带重试的 HTTP JSON 客户端",
        "写一份 Agent 记忆系统设计文档",
        "部署 staging 环境并监控健康状态",
        "整理本周学习笔记",
        "hi",  # 过短，演示失败路径时用 plan 前过滤
    ]


def run_demo_planner(goals: Sequence[str] | None = None) -> list[Plan]:
    """对演示目标批量规划；过短目标跳过。"""
    raw = list(goals) if goals is not None else build_demo_goals()
    plans: list[Plan] = []
    for g in raw:
        try:
            plans.append(plan_from_goal(g))
        except (TypeError, ValueError):
            continue
    return plans


def summarize_plans(plans: Sequence[Plan]) -> dict[str, object]:
    """汇总规划结果。"""
    by_kind: dict[str, int] = {}
    by_complexity: dict[str, int] = {}
    total_steps = 0
    for p in plans:
        by_kind[p.goal_kind] = by_kind.get(p.goal_kind, 0) + 1
        by_complexity[p.complexity] = by_complexity.get(p.complexity, 0) + 1
        total_steps += len(p.steps)
    return {
        "plan_count": len(plans),
        "total_steps": total_steps,
        "avg_steps": (total_steps / len(plans)) if plans else 0.0,
        "by_kind": by_kind,
        "by_complexity": by_complexity,
    }


def render_planner_report(plans: Sequence[Plan] | None = None) -> str:
    """生成含固定二级标题的学习报告。"""
    if plans is None:
        plans = run_demo_planner()
    stats = summarize_plans(plans)
    sample = plans[0] if plans else None
    sample_md = render_plan(sample) if sample else "_（无成功计划）_"

    lines = [
        "# Day 66 报告｜任务分解 Planner",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[0]}",
        "",
        "Planner 把模糊目标变成**有序、可依赖、可验收**的步骤列表，",
        "是 Plan-and-Execute / 多智能体分工的前置积木。",
        "今日用启发式模板代替 LLM，结构与真规划器一致。",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[1]}",
        "",
        "分类：`research` / `coding` / `writing` / `ops` / `generic`。",
        "每类有固定步骤骨架；短且无「并且/然后」的目标裁成 3 步。",
        "步骤 id 形如 `S1`，默认串行依赖 `S(n)` → `S(n-1)`。",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[2]}",
        "",
        f"- 成功规划数：{stats['plan_count']}",
        f"- 总步数：{stats['total_steps']}",
        f"- 平均步数：{stats['avg_steps']:.2f}",
        f"- 按分类：{stats['by_kind']}",
        f"- 按复杂度：{stats['by_complexity']}",
        "",
        "### 样例计划",
        "",
        sample_md,
        f"## {REQUIRED_REPORT_SECTIONS[3]}",
        "",
        "明日 Day 67 会写执行器：按 `Plan.steps` 逐步调用工具，",
        "并把每步结果写回共享状态。Planner 只负责「想清楚」，不负责「做完」。",
        "",
        f"## {REQUIRED_REPORT_SECTIONS[4]}",
        "",
        "Day 67｜Plan-and-Execute：按计划逐步调用工具。",
        "",
    ]
    return "\n".join(lines)
