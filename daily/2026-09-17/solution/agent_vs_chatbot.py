"""参考实现：请先自己完成 exercise/ 再对照。"""

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
    return " ".join(text.split())


def normalize_kind(kind: str) -> str:
    """规范化标签为 chatbot / agent；非法值抛 ValueError。"""
    normalized = kind.strip().lower()
    if normalized not in ALLOWED_KINDS:
        raise ValueError("kind must be 'chatbot' or 'agent'")
    return normalized


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
    _ = needs_multi_step  # 显式忽略：多步推理 alone ≠ Agent
    if needs_tools or has_side_effects:
        return KIND_AGENT
    return KIND_CHATBOT


def validate_comparison_row(row: ComparisonRow) -> None:
    """校验对照表行：维度与两侧说明均非空。"""
    if not normalize_text(row.dimension):
        raise ValueError("dimension must not be empty")
    if not normalize_text(row.chatbot):
        raise ValueError("chatbot description must not be empty")
    if not normalize_text(row.agent):
        raise ValueError("agent description must not be empty")


def validate_scenario(example: ScenarioExample) -> None:
    """校验场景例子。"""
    if not normalize_text(example.title):
        raise ValueError("title must not be empty")
    if not normalize_text(example.user_goal):
        raise ValueError("user_goal must not be empty")
    if not normalize_text(example.rationale):
        raise ValueError("rationale must not be empty")

    kind = normalize_kind(example.expected_kind)
    predicted = classify_by_signals(
        needs_tools=example.needs_tools,
        needs_multi_step=example.needs_multi_step,
        has_side_effects=example.has_side_effects,
    )
    if kind != predicted:
        raise ValueError(
            f"expected_kind {kind!r} inconsistent with signals "
            f"(classified as {predicted!r})"
        )


def default_comparison_rows() -> list[ComparisonRow]:
    """返回默认对照表（至少覆盖 REQUIRED_DIMENSIONS 中的全部维度）。"""
    return [
        ComparisonRow(
            "核心能力",
            "理解与生成文本（答疑、改写、陪聊）",
            "规划目标，调用工具，根据观察继续决策",
        ),
        ComparisonRow(
            "与外部世界交互",
            "通常只读上下文 / 知识，不主动改世界",
            "可读写：API、文件、浏览器、工单系统等",
        ),
        ComparisonRow(
            "控制流",
            "单轮或会话式问答，一次生成结束",
            "Agent Loop：行动 → 观察 → 再行动，直到完成或达上限",
        ),
        ComparisonRow(
            "失败模式",
            "胡说、跑题、风格失控",
            "工具失败、死循环、越权副作用、成本失控",
        ),
        ComparisonRow(
            "评测重点",
            "回答质量、安全、延迟",
            "任务成功率、步数、成本、可审计轨迹",
        ),
    ]


def render_comparison_markdown(rows: list[ComparisonRow]) -> str:
    """渲染 Markdown 表格。"""
    if not rows:
        raise ValueError("rows must not be empty")

    lines = [
        "| 维度 | Chatbot | Agent |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        validate_comparison_row(row)
        lines.append(
            f"| {normalize_text(row.dimension)} | "
            f"{normalize_text(row.chatbot)} | "
            f"{normalize_text(row.agent)} |"
        )
    return "\n".join(lines)


def default_scenarios() -> list[ScenarioExample]:
    """返回若干示例（至少 4 条，且 chatbot / agent 各至少 2 条）。"""
    examples = [
        ScenarioExample(
            title="角色扮演陪聊",
            user_goal="用温柔语气陪我聊天，缓解焦虑",
            needs_tools=False,
            needs_multi_step=False,
            has_side_effects=False,
            expected_kind=KIND_CHATBOT,
            rationale="纯对话生成，无工具、无副作用",
        ),
        ScenarioExample(
            title="CoT 解数学题",
            user_goal="一步步推导这道方程的解",
            needs_tools=False,
            needs_multi_step=True,
            has_side_effects=False,
            expected_kind=KIND_CHATBOT,
            rationale="多步推理仍在文本内完成，不等于行动闭环",
        ),
        ScenarioExample(
            title="查天气再建议穿衣",
            user_goal="查一下上海今天天气，告诉我要不要带伞",
            needs_tools=True,
            needs_multi_step=True,
            has_side_effects=False,
            expected_kind=KIND_AGENT,
            rationale="必须调用天气工具获取外部事实",
        ),
        ScenarioExample(
            title="创建 GitHub Issue",
            user_goal="根据这段 bug 描述创建 issue 并 @ 前端负责人",
            needs_tools=True,
            needs_multi_step=True,
            has_side_effects=True,
            expected_kind=KIND_AGENT,
            rationale="写 Issue 属于外部副作用，必须走工具与权限边界",
        ),
        ScenarioExample(
            title="RAG 文档问答",
            user_goal="根据知识库回答：什么是 overlap 切分",
            needs_tools=False,
            needs_multi_step=False,
            has_side_effects=False,
            expected_kind=KIND_CHATBOT,
            rationale="检索只读组装上下文，按今日定义仍属增强型 Chatbot",
        ),
    ]
    for example in examples:
        validate_scenario(example)
    return examples


def render_examples_report(examples: list[ScenarioExample]) -> str:
    """把例子渲染成可读报告（纯文本即可）。"""
    if not examples:
        raise ValueError("examples must not be empty")

    blocks: list[str] = []
    for index, example in enumerate(examples, start=1):
        validate_scenario(example)
        signals = (
            f"tools={example.needs_tools}, "
            f"multi_step={example.needs_multi_step}, "
            f"side_effects={example.has_side_effects}"
        )
        blocks.append(
            "\n".join(
                [
                    f"## {index}. {normalize_text(example.title)}",
                    f"目标：{normalize_text(example.user_goal)}",
                    f"信号：{signals}",
                    f"标签：{normalize_kind(example.expected_kind)}",
                    f"理由：{normalize_text(example.rationale)}",
                ]
            )
        )
    return "\n\n".join(blocks)
