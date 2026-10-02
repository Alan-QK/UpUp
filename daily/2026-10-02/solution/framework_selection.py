"""参考实现：请先自己完成 exercise/ 再对照。"""

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

_REJECTION_REASONS: dict[str, str] = {
    CANDIDATE_HANDWRITTEN: "当前目标更需要现成编排能力，暂不把纯手写当主路径",
    CANDIDATE_LANGCHAIN: "抽象层偏厚，本阶段优先更聚焦的方案，避免概念过载",
    CANDIDATE_LANGGRAPH: "当前不以复杂状态机/多智能体为主，暂不引入图编排",
    CANDIDATE_OPENAI_AGENTS_SDK: "不想过早绑定单一厂商官方抽象",
    CANDIDATE_LLAMAINDEX: "当前不是 RAG 优先场景，数据索引框架收益有限",
}

_COMPLEMENT: dict[str, str] = {
    CANDIDATE_HANDWRITTEN: CANDIDATE_LANGGRAPH,
    CANDIDATE_LANGGRAPH: CANDIDATE_HANDWRITTEN,
    CANDIDATE_LLAMAINDEX: CANDIDATE_HANDWRITTEN,
    CANDIDATE_OPENAI_AGENTS_SDK: CANDIDATE_HANDWRITTEN,
    CANDIDATE_LANGCHAIN: CANDIDATE_HANDWRITTEN,
}


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
    rejected: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class DecisionCase:
    """一条默认教学案例（上下文 + 期望主选）。"""

    title: str
    context: ProjectContext
    expected_primary: str
    teaching_point: str


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白（含换行）压成单个空格。"""
    return " ".join(text.split())


def normalize_goal(goal: str) -> str:
    """规范化 goal；非法值抛 ValueError。"""
    normalized = goal.strip().lower()
    if normalized not in ALLOWED_GOALS:
        raise ValueError("goal must be one of learn_loop/ship_product/rag_app/multi_agent")
    return normalized


def normalize_level(level: str) -> str:
    """规范化 python_level；非法值抛 ValueError。"""
    normalized = level.strip().lower()
    if normalized not in ALLOWED_LEVELS:
        raise ValueError("level must be beginner/intermediate/advanced")
    return normalized


def normalize_candidate(candidate: str) -> str:
    """规范化候选框架 ID；非法值抛 ValueError。"""
    normalized = candidate.strip().lower()
    if normalized not in ALLOWED_CANDIDATES:
        raise ValueError("candidate is not in the allowed shortlist")
    return normalized


def validate_context(ctx: ProjectContext) -> None:
    """校验项目上下文。"""
    if not normalize_text(ctx.name):
        raise ValueError("name must not be empty")

    goal = normalize_goal(ctx.goal)
    level = normalize_level(ctx.python_level)
    _ = level

    if ctx.max_frameworks not in (1, 2):
        raise ValueError("max_frameworks must be 1 or 2")

    if goal == GOAL_MULTI_AGENT and not ctx.need_multi_agent:
        raise ValueError("need_multi_agent must be True when goal is multi_agent")

    if goal == GOAL_RAG_APP and not ctx.need_rag_first:
        raise ValueError("need_rag_first must be True when goal is rag_app")


def pick_primary(ctx: ProjectContext) -> str:
    """按今日简化规则选出主选。"""
    validate_context(ctx)
    goal = normalize_goal(ctx.goal)
    level = normalize_level(ctx.python_level)

    if goal == GOAL_LEARN_LOOP or level == LEVEL_BEGINNER:
        return CANDIDATE_HANDWRITTEN
    if goal == GOAL_MULTI_AGENT or ctx.need_multi_agent:
        return CANDIDATE_LANGGRAPH
    if goal == GOAL_RAG_APP or ctx.need_rag_first:
        return CANDIDATE_LLAMAINDEX
    if ctx.prefer_official_sdk:
        return CANDIDATE_OPENAI_AGENTS_SDK
    return CANDIDATE_LANGCHAIN


def pick_secondary(ctx: ProjectContext, primary: str) -> str | None:
    """在 max_frameworks 允许时挑选一个互补备胎。"""
    validate_context(ctx)
    primary_id = normalize_candidate(primary)
    if ctx.max_frameworks == 1:
        return None
    complement = _COMPLEMENT.get(primary_id)
    if complement is None or complement == primary_id:
        return None
    return complement


def build_rejection_notes(primary: str, secondary: str | None) -> tuple[tuple[str, str], ...]:
    """为所有未入选候选生成一句弃选理由。"""
    selected = {normalize_candidate(primary)}
    if secondary is not None:
        selected.add(normalize_candidate(secondary))

    notes: list[tuple[str, str]] = []
    for candidate in sorted(ALLOWED_CANDIDATES):
        if candidate in selected:
            continue
        notes.append((candidate, _REJECTION_REASONS[candidate]))
    return tuple(notes)


def recommend_framework(ctx: ProjectContext) -> Recommendation:
    """完整推荐：主选、备胎、理由列表、弃选说明。"""
    validate_context(ctx)
    primary = pick_primary(ctx)
    secondary = pick_secondary(ctx, primary)
    goal = normalize_goal(ctx.goal)

    reasons = (
        f"项目目标 goal={goal}，按少而精规则主选 {primary}",
        f"python_level={normalize_level(ctx.python_level)}，"
        f"max_frameworks={ctx.max_frameworks}，"
        f"备胎={'无' if secondary is None else secondary}",
    )
    rejected = build_rejection_notes(primary, secondary)
    return Recommendation(
        primary=primary,
        secondary=secondary,
        reasons=reasons,
        rejected=rejected,
    )


def render_selection_note(ctx: ProjectContext, rec: Recommendation) -> str:
    """渲染一页选型笔记（Markdown）。"""
    validate_context(ctx)
    if not rec.reasons:
        raise ValueError("reasons must not be empty")

    primary = normalize_candidate(rec.primary)
    secondary = (
        None if rec.secondary is None else normalize_candidate(rec.secondary)
    )

    reason_lines = "\n".join(f"- {normalize_text(r)}" for r in rec.reasons)
    reject_lines = "\n".join(
        f"- `{name}`：{normalize_text(why)}" for name, why in rec.rejected
    )
    secondary_text = "无" if secondary is None else f"`{secondary}`"

    next_step = {
        CANDIDATE_HANDWRITTEN: "巩固手写 Loop，并选一个备胎框架做概念映射",
        CANDIDATE_LANGGRAPH: "用图/状态节点重写 Week10 Agent，对照 max_steps 与 Trace",
        CANDIDATE_LLAMAINDEX: "先打通索引检索，再把检索封装为 Agent 工具",
        CANDIDATE_OPENAI_AGENTS_SDK: "对照官方 Agent/Tool 抽象，复现只读文件助手",
        CANDIDATE_LANGCHAIN: "用最小 Tool + AgentExecutor（或等价 API）复现双工具 Demo",
    }[primary]

    return "\n".join(
        [
            f"# 选型笔记 · {normalize_text(ctx.name)}",
            "",
            f"## {REQUIRED_NOTE_SECTIONS[0]}",
            f"- 名称：{normalize_text(ctx.name)}",
            f"- goal：`{normalize_goal(ctx.goal)}`",
            f"- python_level：`{normalize_level(ctx.python_level)}`",
            f"- need_multi_agent：{ctx.need_multi_agent}",
            f"- need_rag_first：{ctx.need_rag_first}",
            f"- prefer_official_sdk：{ctx.prefer_official_sdk}",
            f"- max_frameworks：{ctx.max_frameworks}",
            "",
            f"## {REQUIRED_NOTE_SECTIONS[1]}",
            f"- 主选：`{primary}`",
            f"- 备胎：{secondary_text}",
            "",
            f"## {REQUIRED_NOTE_SECTIONS[2]}",
            reason_lines,
            "",
            f"## {REQUIRED_NOTE_SECTIONS[3]}",
            reject_lines or "- （无）",
            "",
            f"## {REQUIRED_NOTE_SECTIONS[4]}",
            f"- {next_step}",
        ]
    )


def default_decision_cases() -> list[DecisionCase]:
    """返回至少 4 条默认案例，覆盖 4 种 goal。"""
    cases = [
        DecisionCase(
            title="转型学习：先搞懂 Loop",
            context=ProjectContext(
                name="个人转型练习",
                goal=GOAL_LEARN_LOOP,
                python_level=LEVEL_INTERMEDIATE,
                need_multi_agent=False,
                need_rag_first=False,
                prefer_official_sdk=False,
                max_frameworks=2,
            ),
            expected_primary=CANDIDATE_HANDWRITTEN,
            teaching_point="学习目标优先手写，框架只作对照备胎",
        ),
        DecisionCase(
            title="上线内部助手",
            context=ProjectContext(
                name="内部工具助手",
                goal=GOAL_SHIP_PRODUCT,
                python_level=LEVEL_ADVANCED,
                need_multi_agent=False,
                need_rag_first=False,
                prefer_official_sdk=False,
                max_frameworks=1,
            ),
            expected_primary=CANDIDATE_LANGCHAIN,
            teaching_point="成熟交付且不绑官方 SDK 时，通用编排框架可作主选",
        ),
        DecisionCase(
            title="文档问答优先",
            context=ProjectContext(
                name="文档问答 Bot",
                goal=GOAL_RAG_APP,
                python_level=LEVEL_INTERMEDIATE,
                need_multi_agent=False,
                need_rag_first=True,
                prefer_official_sdk=False,
                max_frameworks=2,
            ),
            expected_primary=CANDIDATE_LLAMAINDEX,
            teaching_point="RAG 优先选数据/索引取向框架，备胎留手写保住 Loop 掌控",
        ),
        DecisionCase(
            title="调研写作多智能体",
            context=ProjectContext(
                name="调研写作流水线",
                goal=GOAL_MULTI_AGENT,
                python_level=LEVEL_ADVANCED,
                need_multi_agent=True,
                need_rag_first=False,
                prefer_official_sdk=False,
                max_frameworks=2,
            ),
            expected_primary=CANDIDATE_LANGGRAPH,
            teaching_point="多智能体/状态机场景优先图编排，而不是先堆聊天链",
        ),
        DecisionCase(
            title="新手想上官方 SDK",
            context=ProjectContext(
                name="新手官方 SDK 冲动",
                goal=GOAL_SHIP_PRODUCT,
                python_level=LEVEL_BEGINNER,
                need_multi_agent=False,
                need_rag_first=False,
                prefer_official_sdk=True,
                max_frameworks=1,
            ),
            expected_primary=CANDIDATE_HANDWRITTEN,
            teaching_point="Python 尚弱时，即使想上线也先手写打底，避免双重陡坡",
        ),
    ]
    for case in cases:
        rec = recommend_framework(case.context)
        if rec.primary != case.expected_primary:
            raise RuntimeError(
                f"case {case.title!r} expected {case.expected_primary}, got {rec.primary}"
            )
    return cases
