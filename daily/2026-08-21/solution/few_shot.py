"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

from dataclasses import dataclass, field


KIND_POSITIVE = "positive"
KIND_COUNTER = "counter"
ALLOWED_KINDS = frozenset({KIND_POSITIVE, KIND_COUNTER})

SECTION_TASK = "任务"
SECTION_LABELS = "标签集合"
SECTION_POSITIVE = "正例"
SECTION_COUNTER = "反例"
SECTION_OUTPUT_FORMAT = "输出格式"

SECTION_ORDER = (
    SECTION_TASK,
    SECTION_LABELS,
    SECTION_POSITIVE,
    SECTION_COUNTER,
    SECTION_OUTPUT_FORMAT,
)


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白（含换行）压成单个空格。"""
    return " ".join(text.split())


def normalize_kind(kind: str) -> str:
    """规范化示例种类。"""
    normalized = kind.strip().lower()
    if normalized not in ALLOWED_KINDS:
        raise ValueError("kind must be 'positive' or 'counter'")
    return normalized


@dataclass(frozen=True)
class ShotExample:
    """一条 few-shot 示例。"""

    text: str
    label: str
    kind: str = KIND_POSITIVE
    note: str | None = None


@dataclass
class ClassificationPrompt:
    """文本分类 few-shot Prompt 规格。"""

    task: str
    labels: list[str]
    examples: list[ShotExample] = field(default_factory=list)
    output_format: str = "只输出一个标签，不要解释"


def _normalized_label_set(labels: list[str]) -> list[str]:
    """保序去重后的有效标签列表。"""
    result: list[str] = []
    seen: set[str] = set()
    for raw in labels:
        item = normalize_text(raw)
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def validate_classification_prompt(spec: ClassificationPrompt) -> None:
    """校验分类 Prompt。"""
    if not normalize_text(spec.task):
        raise ValueError("task must not be empty")
    if not normalize_text(spec.output_format):
        raise ValueError("output_format must not be empty")
    if not isinstance(spec.labels, list):
        raise TypeError("labels must be a list")

    label_set = _normalized_label_set(spec.labels)
    if not label_set:
        raise ValueError("labels must contain at least one non-empty label")

    if not isinstance(spec.examples, list):
        raise TypeError("examples must be a list")

    positive_count = 0
    allowed = set(label_set)
    for example in spec.examples:
        if not normalize_text(example.text):
            raise ValueError("text must not be empty")
        label = normalize_text(example.label)
        if label not in allowed:
            raise ValueError(f"label {label!r} is not in labels")
        kind = normalize_kind(example.kind)
        if kind == KIND_POSITIVE:
            positive_count += 1
        if example.note is not None and not isinstance(example.note, str):
            raise TypeError("note must be a string or None")

    if positive_count < 1:
        raise ValueError("examples must include at least one positive shot")


def format_label_list(labels: list[str]) -> str:
    """把标签列表格式化为 \"a / b / c\"。"""
    return " / ".join(_normalized_label_set(labels))


def format_shot(example: ShotExample, *, index: int) -> str:
    """格式化单条示例。"""
    text = normalize_text(example.text)
    label = normalize_text(example.label)
    lines = [f"{index}. 输入：{text}", f"   标签：{label}"]
    if example.note is not None:
        note = normalize_text(example.note)
        if note:
            lines.append(f"   说明：{note}")
    return "\n".join(lines)


def render_examples_block(examples: list[ShotExample], *, kind: str) -> str:
    """渲染某一 kind 的示例块。"""
    target = normalize_kind(kind)
    blocks: list[str] = []
    index = 0
    for example in examples:
        if normalize_kind(example.kind) != target:
            continue
        index += 1
        blocks.append(format_shot(example, index=index))
    return "\n".join(blocks)


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


def render_system_prompt(spec: ClassificationPrompt) -> str:
    """把 ClassificationPrompt 渲染为 system 文本。"""
    validate_classification_prompt(spec)

    task = normalize_text(spec.task)
    labels_body = format_label_list(spec.labels)
    positive_body = render_examples_block(spec.examples, kind=KIND_POSITIVE)
    counter_body = render_examples_block(spec.examples, kind=KIND_COUNTER)
    output_format = normalize_text(spec.output_format)

    mapping = {
        SECTION_TASK: task,
        SECTION_LABELS: labels_body,
        SECTION_POSITIVE: positive_body,
        SECTION_COUNTER: counter_body,
        SECTION_OUTPUT_FORMAT: output_format,
    }
    sections = [(name, mapping[name]) for name in SECTION_ORDER]
    return join_sections(sections)


def render_user_prompt(user_text: str, *, label: str = "待分类文本") -> str:
    """渲染 user 消息正文。"""
    normalized = normalize_text(user_text)
    if not normalized:
        raise ValueError("user_text must not be empty")
    label_clean = label.strip() or "待分类文本"
    return f"【{label_clean}】\n{normalized}"


def build_classification_messages(
    spec: ClassificationPrompt,
    user_text: str,
    *,
    user_label: str = "待分类文本",
) -> list[dict[str, str]]:
    """组装 OpenAI 风格 messages。"""
    return [
        {"role": "system", "content": render_system_prompt(spec)},
        {
            "role": "user",
            "content": render_user_prompt(user_text, label=user_label),
        },
    ]
