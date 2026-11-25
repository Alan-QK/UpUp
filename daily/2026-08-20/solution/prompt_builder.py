"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

from dataclasses import dataclass, field


SECTION_ROLE = "角色"
SECTION_TASK = "任务"
SECTION_CONSTRAINTS = "约束"
SECTION_OUTPUT_FORMAT = "输出格式"
SECTION_CONTEXT = "上下文"

SECTION_ORDER = (
    SECTION_ROLE,
    SECTION_TASK,
    SECTION_CONSTRAINTS,
    SECTION_OUTPUT_FORMAT,
    SECTION_CONTEXT,
)


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白（含换行）压成单个空格。"""
    return " ".join(text.split())


def format_constraints(constraints: list[str]) -> str:
    """把约束列表格式化为 Markdown 无序列表。"""
    items: list[str] = []
    for raw in constraints:
        item = normalize_text(raw)
        if item:
            items.append(f"- {item}")
    return "\n".join(items)


def join_sections(sections: list[tuple[str, str]]) -> str:
    """按给定列表拼装章节。"""
    blocks: list[str] = []
    for title, body in sections:
        title_clean = title.strip()
        body_clean = body.strip()
        if not title_clean or not body_clean:
            continue
        blocks.append(f"【{title_clean}】\n{body_clean}")
    return "\n\n".join(blocks)


@dataclass
class PromptSpec:
    """结构化 Prompt 规格。"""

    role: str
    task: str
    output_format: str
    constraints: list[str] = field(default_factory=list)
    context: str | None = None


def validate_spec(spec: PromptSpec) -> None:
    """校验必填字段。"""
    if not normalize_text(spec.role):
        raise ValueError("role must not be empty")
    if not normalize_text(spec.task):
        raise ValueError("task must not be empty")
    if not normalize_text(spec.output_format):
        raise ValueError("output_format must not be empty")
    if not isinstance(spec.constraints, list):
        raise TypeError("constraints must be a list")


def render_system_prompt(spec: PromptSpec) -> str:
    """把 PromptSpec 渲染为 system 文本。"""
    validate_spec(spec)

    role = normalize_text(spec.role)
    task = normalize_text(spec.task)
    output_format = normalize_text(spec.output_format)
    constraints_body = format_constraints(spec.constraints)
    context_body = ""
    if spec.context is not None:
        context_body = normalize_text(spec.context)

    mapping = {
        SECTION_ROLE: role,
        SECTION_TASK: task,
        SECTION_CONSTRAINTS: constraints_body,
        SECTION_OUTPUT_FORMAT: output_format,
        SECTION_CONTEXT: context_body,
    }
    sections = [(name, mapping[name]) for name in SECTION_ORDER]
    return join_sections(sections)


def render_user_prompt(user_input: str, *, label: str = "用户输入") -> str:
    """渲染 user 消息正文。"""
    normalized = normalize_text(user_input)
    if not normalized:
        raise ValueError("user_input must not be empty")
    label_clean = label.strip() or "用户输入"
    return f"【{label_clean}】\n{normalized}"


def build_chat_messages(
    spec: PromptSpec,
    user_input: str,
    *,
    user_label: str = "用户输入",
) -> list[dict[str, str]]:
    """组装 OpenAI 风格 messages。"""
    return [
        {"role": "system", "content": render_system_prompt(spec)},
        {
            "role": "user",
            "content": render_user_prompt(user_input, label=user_label),
        },
    ]
