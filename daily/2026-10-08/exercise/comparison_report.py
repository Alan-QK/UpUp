"""Day 55 练习：手写 Agent vs 框架层对比报告生成器。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——今天是「认知沉淀报告」，不是真装框架。
"""

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
    # TODO: 实现规范化
    raise NotImplementedError


def normalize_approach(approach: str) -> str:
    """规范化 approach；非法值抛 ValueError。"""
    # TODO: strip + lower，校验属于 ALLOWED_APPROACHES
    raise NotImplementedError


def normalize_dimension(dimension: str) -> str:
    """规范化 dimension；非法值抛 ValueError。"""
    # TODO
    raise NotImplementedError


def normalize_goal(goal: str) -> str:
    """规范化 goal；非法值抛 ValueError。"""
    # TODO
    raise NotImplementedError


def validate_score_value(value: int) -> None:
    """分数必须是 1–5 的 int，否则 ValueError。"""
    # TODO
    raise NotImplementedError


def validate_dimension_score(score: DimensionScore) -> None:
    """校验单条 DimensionScore：维度合法、两侧分数合法、note 非空。"""
    # TODO
    raise NotImplementedError


def week11_default_scores() -> tuple[DimensionScore, ...]:
    """返回 Week 11 教学用的默认六维评分（顺序固定为 ALLOWED 的稳定顺序）。

    期望（便于对照测试）：
    - control:     handwritten 5 / framework 3
    - clarity:     handwritten 5 / framework 3
    - velocity:    handwritten 2 / framework 5
    - extensibility: handwritten 3 / framework 4
    - debug:       handwritten 5 / framework 3
    - lockin_safety: handwritten 5 / framework 2

    note 用中文短句说明「为什么这样打」。
    """
    # TODO: 构造 6 条 DimensionScore，覆盖全部 ALLOWED_DIMENSIONS
    raise NotImplementedError


def score_delta(score: DimensionScore) -> int:
    """handwritten - framework；正数表示手写领先。"""
    # TODO: 先 validate_dimension_score
    raise NotImplementedError


def summarize_side_wins(scores: tuple[DimensionScore, ...] | list[DimensionScore]) -> SideWins:
    """按维度比较两侧分数，归类到手写赢 / 框架赢 / 平局。"""
    # TODO
    raise NotImplementedError


def recommend_for_goal(goal: str) -> str:
    """按目标给出主选 approach。

    规则：
    - learn_loop / interview → handwritten
    - ship_product / onboard → framework
    """
    # TODO
    raise NotImplementedError


def recommendation_reason(goal: str) -> str:
    """给 recommend_for_goal 配一句中文理由（非空）。"""
    # TODO
    raise NotImplementedError


def render_score_table(scores: tuple[DimensionScore, ...] | list[DimensionScore]) -> str:
    """渲染 Markdown 表格：维度 | 手写 | 框架 | 说明。"""
    # TODO: 表头 + 分隔行 + 每维一行；维度列用 DIMENSION_LABELS
    raise NotImplementedError


def render_comparison_report(
    goal: str,
    scores: tuple[DimensionScore, ...] | list[DimensionScore] | None = None,
    title: str = "Week 11 · 手写 vs 框架对比报告",
) -> str:
    """渲染完整对比报告 Markdown。

    必须包含 REQUIRED_REPORT_SECTIONS 全部二级标题（## ...）。
    scores 默认使用 week11_default_scores()。
    """
    # TODO
    raise NotImplementedError
