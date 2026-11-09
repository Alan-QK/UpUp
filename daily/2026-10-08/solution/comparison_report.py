"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

from dataclasses import dataclass

APPROACH_HANDWRITTEN = "handwritten"
APPROACH_FRAMEWORK = "framework"
ALLOWED_APPROACHES = frozenset({APPROACH_HANDWRITTEN, APPROACH_FRAMEWORK})

DIMENSION_CONTROL = "control"
DIMENSION_CLARITY = "clarity"
DIMENSION_VELOCITY = "velocity"
DIMENSION_EXTENSIBILITY = "extensibility"
DIMENSION_DEBUG = "debug"
DIMENSION_LOCKIN = "lockin_safety"
ALLOWED_DIMENSIONS = frozenset(
    {
        DIMENSION_CONTROL,
        DIMENSION_CLARITY,
        DIMENSION_VELOCITY,
        DIMENSION_EXTENSIBILITY,
        DIMENSION_DEBUG,
        DIMENSION_LOCKIN,
    }
)

DIMENSION_LABELS: dict[str, str] = {
    DIMENSION_CONTROL: "可控性",
    DIMENSION_CLARITY: "概念清晰度",
    DIMENSION_VELOCITY: "落地速度",
    DIMENSION_EXTENSIBILITY: "扩展顺滑度",
    DIMENSION_DEBUG: "排错友好度",
    DIMENSION_LOCKIN: "锁定安全性",
}

GOAL_LEARN_LOOP = "learn_loop"
GOAL_SHIP_PRODUCT = "ship_product"
GOAL_INTERVIEW = "interview"
GOAL_ONBOARD = "onboard"
ALLOWED_GOALS = frozenset(
    {GOAL_LEARN_LOOP, GOAL_SHIP_PRODUCT, GOAL_INTERVIEW, GOAL_ONBOARD}
)

REQUIRED_REPORT_SECTIONS = (
    "本周回顾",
    "对照维度",
    "手写优势",
    "框架优势",
    "决策建议",
    "下周预告",
)

WEEK11_RETROSPECTIVE = (
    ("51", "框架选型原则：少而精，先手写再抽象"),
    ("52", "迷你框架对照重写：Tool / Registry / Runner"),
    ("53", "自定义业务工具接入框架风格 API"),
    ("54", "流式事件 tool_start/tool_end 与 UI 状态派生"),
)

_DIMENSION_ORDER = (
    DIMENSION_CONTROL,
    DIMENSION_CLARITY,
    DIMENSION_VELOCITY,
    DIMENSION_EXTENSIBILITY,
    DIMENSION_DEBUG,
    DIMENSION_LOCKIN,
)

_DEFAULT_SCORE_ROWS: dict[str, tuple[int, int, str]] = {
    DIMENSION_CONTROL: (5, 3, "Loop/终止/白名单全在自己手里"),
    DIMENSION_CLARITY: (5, 3, "messages 与 tool_calls 路径直观"),
    DIMENSION_VELOCITY: (2, 5, "框架省去样板，同类能力落地更快"),
    DIMENSION_EXTENSIBILITY: (3, 4, "约定成熟时加工具/事件更顺"),
    DIMENSION_DEBUG: (5, 3, "堆栈与状态无框架中间层遮挡"),
    DIMENSION_LOCKIN: (5, 2, "不绑特定库与厂商抽象"),
}

_GOAL_REASONS: dict[str, str] = {
    GOAL_LEARN_LOOP: "学习阶段要看见 Loop 细节，手写更能建立可迁移心智模型",
    GOAL_INTERVIEW: "面试需要能指着代码讲清 Agent 如何跑，而不是只会调库",
    GOAL_SHIP_PRODUCT: "交付场景优先约定与脚手架，框架能放大协作与速度",
    GOAL_ONBOARD: "带新人需要统一抽象与文档路径，框架层降低各自发明轮子",
}


@dataclass(frozen=True)
class DimensionScore:
    """某一维度上 handwritten / framework 的 1–5 分与短注。"""

    dimension: str
    handwritten: int
    framework: int
    note: str


@dataclass(frozen=True)
class SideWins:
    """两侧各自赢下的维度列表（维度 ID）。"""

    handwritten: tuple[str, ...]
    framework: tuple[str, ...]
    ties: tuple[str, ...]


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白（含换行）压成单个空格。"""
    return " ".join(text.split())


def normalize_approach(approach: str) -> str:
    """规范化 approach；非法值抛 ValueError。"""
    normalized = approach.strip().lower()
    if normalized not in ALLOWED_APPROACHES:
        raise ValueError("approach must be handwritten or framework")
    return normalized


def normalize_dimension(dimension: str) -> str:
    """规范化 dimension；非法值抛 ValueError。"""
    normalized = dimension.strip().lower()
    if normalized not in ALLOWED_DIMENSIONS:
        raise ValueError("dimension is not in the allowed set")
    return normalized


def normalize_goal(goal: str) -> str:
    """规范化 goal；非法值抛 ValueError。"""
    normalized = goal.strip().lower()
    if normalized not in ALLOWED_GOALS:
        raise ValueError("goal must be learn_loop/ship_product/interview/onboard")
    return normalized


def validate_score_value(value: int) -> None:
    """分数必须是 1–5 的 int，否则 ValueError。"""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("score must be an int from 1 to 5")
    if value < 1 or value > 5:
        raise ValueError("score must be an int from 1 to 5")


def validate_dimension_score(score: DimensionScore) -> None:
    """校验单条 DimensionScore：维度合法、两侧分数合法、note 非空。"""
    normalize_dimension(score.dimension)
    validate_score_value(score.handwritten)
    validate_score_value(score.framework)
    if not normalize_text(score.note):
        raise ValueError("note must not be empty")


def week11_default_scores() -> tuple[DimensionScore, ...]:
    """返回 Week 11 教学用的默认六维评分。"""
    rows: list[DimensionScore] = []
    for dimension in _DIMENSION_ORDER:
        handwritten, framework, note = _DEFAULT_SCORE_ROWS[dimension]
        score = DimensionScore(
            dimension=dimension,
            handwritten=handwritten,
            framework=framework,
            note=note,
        )
        validate_dimension_score(score)
        rows.append(score)
    return tuple(rows)


def score_delta(score: DimensionScore) -> int:
    """handwritten - framework；正数表示手写领先。"""
    validate_dimension_score(score)
    return score.handwritten - score.framework


def summarize_side_wins(scores: tuple[DimensionScore, ...] | list[DimensionScore]) -> SideWins:
    """按维度比较两侧分数，归类到手写赢 / 框架赢 / 平局。"""
    if not scores:
        raise ValueError("scores must not be empty")

    handwritten_wins: list[str] = []
    framework_wins: list[str] = []
    ties: list[str] = []
    seen: set[str] = set()

    for score in scores:
        validate_dimension_score(score)
        dimension = normalize_dimension(score.dimension)
        if dimension in seen:
            raise ValueError(f"duplicate dimension: {dimension}")
        seen.add(dimension)
        delta = score_delta(score)
        if delta > 0:
            handwritten_wins.append(dimension)
        elif delta < 0:
            framework_wins.append(dimension)
        else:
            ties.append(dimension)

    missing = ALLOWED_DIMENSIONS - seen
    if missing:
        raise ValueError(f"missing dimensions: {sorted(missing)}")

    return SideWins(
        handwritten=tuple(handwritten_wins),
        framework=tuple(framework_wins),
        ties=tuple(ties),
    )


def recommend_for_goal(goal: str) -> str:
    """按目标给出主选 approach。"""
    normalized = normalize_goal(goal)
    if normalized in {GOAL_LEARN_LOOP, GOAL_INTERVIEW}:
        return APPROACH_HANDWRITTEN
    return APPROACH_FRAMEWORK


def recommendation_reason(goal: str) -> str:
    """给 recommend_for_goal 配一句中文理由（非空）。"""
    normalized = normalize_goal(goal)
    return _GOAL_REASONS[normalized]


def render_score_table(scores: tuple[DimensionScore, ...] | list[DimensionScore]) -> str:
    """渲染 Markdown 表格：维度 | 手写 | 框架 | 说明。"""
    if not scores:
        raise ValueError("scores must not be empty")

    lines = [
        "| 维度 | 手写 | 框架 | 说明 |",
        "|------|------|------|------|",
    ]
    for score in scores:
        validate_dimension_score(score)
        label = DIMENSION_LABELS[normalize_dimension(score.dimension)]
        note = normalize_text(score.note)
        lines.append(
            f"| {label} | {score.handwritten} | {score.framework} | {note} |"
        )
    return "\n".join(lines)


def _format_win_list(dimensions: tuple[str, ...]) -> str:
    if not dimensions:
        return "- （本报告无单独领先维度）"
    return "\n".join(
        f"- {DIMENSION_LABELS[normalize_dimension(item)]}（`{item}`）"
        for item in dimensions
    )


def render_comparison_report(
    goal: str,
    scores: tuple[DimensionScore, ...] | list[DimensionScore] | None = None,
    title: str = "Week 11 · 手写 vs 框架对比报告",
) -> str:
    """渲染完整对比报告 Markdown。"""
    normalized_goal = normalize_goal(goal)
    resolved_scores = tuple(scores) if scores is not None else week11_default_scores()
    wins = summarize_side_wins(resolved_scores)
    winner = recommend_for_goal(normalized_goal)
    reason = recommendation_reason(normalized_goal)

    retro_lines = "\n".join(
        f"- Day {day}：{summary}" for day, summary in WEEK11_RETROSPECTIVE
    )
    table = render_score_table(resolved_scores)

    winner_label = "手写 Agent" if winner == APPROACH_HANDWRITTEN else "框架层 Agent"

    parts = [
        f"# {normalize_text(title)}",
        "",
        "## 本周回顾",
        "",
        retro_lines,
        "",
        "## 对照维度",
        "",
        table,
        "",
        "## 手写优势",
        "",
        _format_win_list(wins.handwritten),
        "",
        "## 框架优势",
        "",
        _format_win_list(wins.framework),
        "",
        "## 决策建议",
        "",
        f"- 目标：`{normalized_goal}`",
        f"- 主选：`{winner}`（{winner_label}）",
        f"- 理由：{reason}",
        "",
        "## 下周预告",
        "",
        "- Day 56 起进入 Week 12：Prompt Injection、工具校验、测试与 HITL",
        "- 阶段里程碑：打磨可验收的 `tool-agent`",
        "",
    ]
    return "\n".join(parts)
