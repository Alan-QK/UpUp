"""Day 66 练习：任务分解 Planner（目标 → 步骤列表）。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——不调用 LLM。

提示：
- 先实现 normalize / classify / estimate
- 再用模板拼 PlanStep（默认串行依赖）
- 最后做 render / demo / report
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

# 以下正则已给齐，分类请直接复用，勿改语义。
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
    # TODO: 非 str 抛 TypeError；用正则把连续空白压成单空格并 strip
    raise NotImplementedError


def classify_goal(goal: str) -> str:
    """按关键词启发式分类目标。

    优先级（从高到低）：coding → writing → ops → research → generic
    过短（normalize 后 < MIN_GOAL_LEN）抛 ValueError。
    """
    # TODO
    raise NotImplementedError


def estimate_complexity(goal: str, step_count: int) -> str:
    """根据目标措辞与步数估复杂度。

    - simple：步数 <= 3 且无复杂提示词且 normalize 后长度 < 24
    - complex：步数 >= 7 或复杂提示词命中次数 >= 2 或长度 > 80
    - 其余 medium
    """
    # TODO
    raise NotImplementedError


def _clamp_max_steps(max_steps: int) -> int:
    """校验 max_steps 类型与区间 [MIN_MAX_STEPS, MAX_MAX_STEPS]。"""
    # TODO: bool 也要拒绝（isinstance(True, int) 为 True）
    raise NotImplementedError


def _templates(goal: str, kind: str) -> list[tuple[str, str, str]]:
    """返回 (title, detail, step_kind) 模板列表。

    至少 5 条；具体文案可参考 solution，但测试主要看结构与分类。
    """
    # TODO: 按 kind 返回不同骨架；generic 兜底
    raise NotImplementedError


def _build_steps(
    templates: Sequence[tuple[str, str, str]],
    max_steps: int,
) -> tuple[PlanStep, ...]:
    """截取前 max_steps 条，生成 S1..Sn，且 Si 依赖 S(i-1)。"""
    # TODO
    raise NotImplementedError


def plan_from_goal(goal: str, *, max_steps: int = DEFAULT_MAX_STEPS) -> Plan:
    """把自然语言目标拆成有序步骤列表。

    规则：
    1. clamp max_steps
    2. normalize；过短抛 ValueError
    3. classify
    4. 若目标短（<20）且无复杂提示词且 max_steps>3 → effective_max=3
    5. 组装 Plan，strategy 形如 heuristic:<kind>
    """
    # TODO
    raise NotImplementedError


def render_plan(plan: Plan) -> str:
    """把计划渲染成 Markdown（含目标、分类、步骤列表）。"""
    # TODO
    raise NotImplementedError


def build_demo_goals() -> list[str]:
    """返回一批演示目标（可含一条过短目标）。"""
    # TODO
    raise NotImplementedError


def run_demo_planner(goals: Sequence[str] | None = None) -> list[Plan]:
    """批量规划；TypeError/ValueError 的目标跳过。"""
    # TODO
    raise NotImplementedError


def summarize_plans(plans: Sequence[Plan]) -> dict[str, object]:
    """返回 plan_count / total_steps / avg_steps / by_kind / by_complexity。"""
    # TODO
    raise NotImplementedError


def render_planner_report(plans: Sequence[Plan] | None = None) -> str:
    """生成报告；必须包含 REQUIRED_REPORT_SECTIONS 中每个标题（作 ## 二级标题）。"""
    # TODO
    raise NotImplementedError
