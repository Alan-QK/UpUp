"""Day 41 练习：Chatbot vs Agent 对照表与场景分类。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库。
"""

from __future__ import annotations

from dataclasses import dataclass

KIND_CHATBOT = "chatbot"
KIND_AGENT = "agent"
ALLOWED_KINDS = frozenset({KIND_CHATBOT, KIND_AGENT})

REQUIRED_DIMENSIONS = (
    "核心能力",
    "与外部世界交互",
    "控制流",
    "失败模式",
    "评测重点",
)


@dataclass(frozen=True)
class ComparisonRow:
    """对照表的一行。"""

    dimension: str
    chatbot: str
    agent: str


@dataclass(frozen=True)
class ScenarioExample:
    """一条带信号与期望标签的场景例子。"""

    title: str
    user_goal: str
    needs_tools: bool
    needs_multi_step: bool
    has_side_effects: bool
    expected_kind: str
    rationale: str


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白（含换行）压成单个空格。"""
    # TODO: 实现规范化
    raise NotImplementedError


def normalize_kind(kind: str) -> str:
    """规范化标签为 chatbot / agent；非法值抛 ValueError。"""
    # TODO: strip + lower，校验属于 ALLOWED_KINDS
    raise NotImplementedError


def classify_by_signals(
    *,
    needs_tools: bool,
    needs_multi_step: bool,
    has_side_effects: bool,
) -> str:
    """按信号判定种类。

    规则（刻意简化）：
    - 只要 needs_tools 或 has_side_effects → agent
    - 否则 → chatbot
    - needs_multi_step **单独**不升级为 agent（CoT ≠ Agent）
    """
    # TODO: 实现；needs_multi_step 参数保留供调用方传参，但分类时忽略
    raise NotImplementedError


def validate_comparison_row(row: ComparisonRow) -> None:
    """校验对照表行：维度与两侧说明均非空。"""
    # TODO: 空字符串 / 纯空白 → ValueError
    raise NotImplementedError


def validate_scenario(example: ScenarioExample) -> None:
    """校验场景例子。

    - title / user_goal / rationale 非空
    - expected_kind 合法
    - expected_kind 必须等于 classify_by_signals(...) 的结果
    """
    # TODO: 实现一致性校验
    raise NotImplementedError


def default_comparison_rows() -> list[ComparisonRow]:
    """返回默认对照表（至少覆盖 REQUIRED_DIMENSIONS 中的全部维度）。"""
    # TODO: 返回 ≥5 行，dimension 必须包含 REQUIRED_DIMENSIONS 全部
    raise NotImplementedError


def render_comparison_markdown(rows: list[ComparisonRow]) -> str:
    """渲染 Markdown 表格。

    表头固定为：| 维度 | Chatbot | Agent |
    第二行为分隔行：| --- | --- | --- |
    之后每行一个 ComparisonRow。
    空列表抛 ValueError。
    """
    # TODO: 先 validate 每一行，再拼接
    raise NotImplementedError


def default_scenarios() -> list[ScenarioExample]:
    """返回若干示例（至少 4 条，且 chatbot / agent 各至少 2 条）。"""
    # TODO: 写具体例子；每条都要通过 validate_scenario
    raise NotImplementedError


def render_examples_report(examples: list[ScenarioExample]) -> str:
    """把例子渲染成可读报告（纯文本即可）。

    每条至少包含：标题、目标、信号摘要、标签、理由。
    空列表抛 ValueError。
    """
    # TODO: 先 validate 每条，再拼接
    raise NotImplementedError
