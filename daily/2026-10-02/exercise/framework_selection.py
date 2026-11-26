"""Day 51 练习：Agent 框架选型（少而精）决策器。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——今天是「选型笔记」，不是真装框架。
"""

from __future__ import annotations

from dataclasses import dataclass

GOAL_LEARN_LOOP = "learn_loop"
GOAL_SHIP_PRODUCT = "ship_product"
GOAL_RAG_APP = "rag_app"
GOAL_MULTI_AGENT = "multi_agent"
ALLOWED_GOALS = frozenset(
    {GOAL_LEARN_LOOP, GOAL_SHIP_PRODUCT, GOAL_RAG_APP, GOAL_MULTI_AGENT}
)

LEVEL_BEGINNER = "beginner"
LEVEL_INTERMEDIATE = "intermediate"
LEVEL_ADVANCED = "advanced"
ALLOWED_LEVELS = frozenset(
    {LEVEL_BEGINNER, LEVEL_INTERMEDIATE, LEVEL_ADVANCED}
)

CANDIDATE_HANDWRITTEN = "handwritten"
CANDIDATE_LANGCHAIN = "langchain"
CANDIDATE_LANGGRAPH = "langgraph"
CANDIDATE_OPENAI_AGENTS_SDK = "openai_agents_sdk"
CANDIDATE_LLAMAINDEX = "llamaindex"
ALLOWED_CANDIDATES = frozenset(
    {
        CANDIDATE_HANDWRITTEN,
        CANDIDATE_LANGCHAIN,
        CANDIDATE_LANGGRAPH,
        CANDIDATE_OPENAI_AGENTS_SDK,
        CANDIDATE_LLAMAINDEX,
    }
)

REQUIRED_NOTE_SECTIONS = (
    "项目目标",
    "推荐结论",
    "选择理由",
    "弃选说明",
    "下一步",
)


@dataclass(frozen=True)
class ProjectContext:
    """一次选型所面对的项目上下文。"""

    name: str
    goal: str
    python_level: str
    need_multi_agent: bool
    need_rag_first: bool
    prefer_official_sdk: bool
    max_frameworks: int


@dataclass(frozen=True)
class Recommendation:
    """选型结果：主选 + 可选备胎 + 理由。"""

    primary: str
    secondary: str | None
    reasons: tuple[str, ...]
    rejected: tuple[tuple[str, str], ...]  # (candidate, why_rejected)


@dataclass(frozen=True)
class DecisionCase:
    """一条默认教学案例（上下文 + 期望主选）。"""

    title: str
    context: ProjectContext
    expected_primary: str
    teaching_point: str


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白（含换行）压成单个空格。"""
    # TODO: 实现规范化
    raise NotImplementedError


def normalize_goal(goal: str) -> str:
    """规范化 goal；非法值抛 ValueError。"""
    # TODO: strip + lower，校验属于 ALLOWED_GOALS
    raise NotImplementedError


def normalize_level(level: str) -> str:
    """规范化 python_level；非法值抛 ValueError。"""
    # TODO: strip + lower，校验属于 ALLOWED_LEVELS
    raise NotImplementedError


def normalize_candidate(candidate: str) -> str:
    """规范化候选框架 ID；非法值抛 ValueError。"""
    # TODO: strip + lower，校验属于 ALLOWED_CANDIDATES
    raise NotImplementedError


def validate_context(ctx: ProjectContext) -> None:
    """校验项目上下文。

    - name 非空
    - goal / python_level 合法
    - max_frameworks 只能是 1 或 2
    - 若 goal == multi_agent，则 need_multi_agent 必须为 True
    - 若 goal == rag_app，则 need_rag_first 必须为 True
    """
    # TODO: 实现
    raise NotImplementedError


def pick_primary(ctx: ProjectContext) -> str:
    """按今日简化规则选出主选。

    优先级（从上到下，命中即返回）：
    1. goal == learn_loop 或 python_level == beginner → handwritten
    2. goal == multi_agent 或 need_multi_agent → langgraph
    3. goal == rag_app 或 need_rag_first → llamaindex
    4. prefer_official_sdk → openai_agents_sdk
    5. 否则 → langchain
    """
    # TODO: 先 validate_context，再按规则返回
    raise NotImplementedError


def pick_secondary(ctx: ProjectContext, primary: str) -> str | None:
    """在 max_frameworks 允许时挑选一个互补备胎。

    规则：
    - max_frameworks == 1 → None
    - 否则按互补表挑选，且不得等于 primary：
      handwritten → langgraph
      langgraph → handwritten
      llamaindex → handwritten
      openai_agents_sdk → handwritten
      langchain → handwritten
    - 若互补项与 primary 相同（理论上不应发生）→ None
    """
    # TODO: 实现
    raise NotImplementedError


def build_rejection_notes(primary: str, secondary: str | None) -> tuple[tuple[str, str], ...]:
    """为所有未入选候选生成一句弃选理由。

    - 跳过 primary 与 secondary
    - 每个候选一句固定、可读的中文理由（非空）
    - 返回按候选名字母序排序的元组
    """
    # TODO: 实现
    raise NotImplementedError


def recommend_framework(ctx: ProjectContext) -> Recommendation:
    """完整推荐：主选、备胎、理由列表、弃选说明。

    reasons 至少 2 条，且应提到 goal 与 primary。
    """
    # TODO: 组合 pick_primary / pick_secondary / build_rejection_notes
    raise NotImplementedError


def render_selection_note(ctx: ProjectContext, rec: Recommendation) -> str:
    """渲染一页选型笔记（Markdown）。

    必须包含 REQUIRED_NOTE_SECTIONS 中的全部小标题（用 ## 二级标题）。
    空 reasons 抛 ValueError。
    """
    # TODO: 先 validate，再拼接
    raise NotImplementedError


def default_decision_cases() -> list[DecisionCase]:
    """返回至少 4 条默认案例，覆盖 4 种 goal，且 expected_primary 与推荐一致。"""
    # TODO: 写具体案例；每条 recommend_framework(ctx).primary == expected_primary
    raise NotImplementedError
