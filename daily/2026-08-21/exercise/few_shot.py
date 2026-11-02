"""Day 22 练习：Few-shot 与反例（文本分类 Prompt）。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库。
"""

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

# 固定章节顺序（渲染时按此顺序；空章节跳过）
SECTION_ORDER = (
    SECTION_TASK,
    SECTION_LABELS,
    SECTION_POSITIVE,
    SECTION_COUNTER,
    SECTION_OUTPUT_FORMAT,
)


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白（含换行）压成单个空格。

    例：\"  你好\\n\\n世界  \" → \"你好 世界\"
    """
    # TODO: 实现空白规范化
    raise NotImplementedError


def normalize_kind(kind: str) -> str:
    """规范化示例种类。

    - strip + lower
    - 结果必须属于 ALLOWED_KINDS，否则 ValueError（消息含 \"kind\"）
    """
    # TODO: 实现 kind 规范化
    raise NotImplementedError


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


def validate_classification_prompt(spec: ClassificationPrompt) -> None:
    """校验分类 Prompt。

    规则：
    - task / output_format：normalize 后不得为空，否则 ValueError
      （消息分别含 \"task\" / \"output_format\"）
    - labels：必须是非空 list；每项 normalize 后非空；去重后至少 1 个
      （重复标签以首次出现为准，校验阶段允许传入重复，但逻辑上集合非空）
    - examples：必须是 list；至少 1 条 kind 规范化后为 positive 的有效示例
    - 每条示例：
      - text normalize 后非空，否则 ValueError（含 \"text\"）
      - label normalize 后必须落在 labels 规范化集合内，否则 ValueError（含 \"label\"）
      - kind 必须可被 normalize_kind 接受
      - note 可为 None；若为 str，允许空白（渲染时忽略空白 note）
    """
    # TODO: 实现校验
    raise NotImplementedError


def format_label_list(labels: list[str]) -> str:
    """把标签列表格式化为 \"a / b / c\"。

    - 逐项 normalize_text；跳过空项
    - 保序去重
    - 若有效项为空，返回 \"\"
    """
    # TODO: 实现标签列表格式化
    raise NotImplementedError


def format_shot(example: ShotExample, *, index: int) -> str:
    """格式化单条示例。

    形态：
      {index}. 输入：{text}
         标签：{label}

    若 note 存在且 normalize 后非空，再追加一行：
         说明：{note}

    注意：
    - index 从 1 开始由调用方传入
    - text/label/note 都先 normalize_text（note 为空则不输出说明行）
    - 「标签」「说明」行相对「输入」行缩进 3 个空格
    """
    # TODO: 实现单条示例格式化
    raise NotImplementedError


def render_examples_block(examples: list[ShotExample], *, kind: str) -> str:
    """渲染某一 kind 的示例块。

    - kind 先走 normalize_kind
    - 只保留 kind 匹配的示例（比较时用规范化后的 kind）
    - 按原列表顺序编号：1..n（只对匹配项编号）
    - 多条之间用单个换行连接
    - 若无匹配项，返回 \"\"
    """
    # TODO: 实现按 kind 过滤并渲染
    raise NotImplementedError


def join_sections(sections: list[tuple[str, str]]) -> str:
    """按给定列表拼装章节。

    每个元素是 (标题, 正文)。
    - 标题 strip；正文 strip 后为空则整章节跳过
    - 保留的章节形如：
      【标题】
      正文
    - 章节之间用两个换行分隔
    - 若全部跳过，返回 \"\"
    """
    # TODO: 实现章节拼装
    raise NotImplementedError


def render_system_prompt(spec: ClassificationPrompt) -> str:
    """把 ClassificationPrompt 渲染为 system 文本。

    步骤：
    1. validate_classification_prompt(spec)
    2. 按 SECTION_ORDER 组装：
       - 任务 ← normalize(spec.task)
       - 标签集合 ← format_label_list(spec.labels)
       - 正例 ← render_examples_block(..., kind=positive)
       - 反例 ← render_examples_block(..., kind=counter)
       - 输出格式 ← normalize(spec.output_format)
    3. 返回 join_sections(...)
    """
    # TODO: 实现 system 渲染
    raise NotImplementedError


def render_user_prompt(user_text: str, *, label: str = "待分类文本") -> str:
    """渲染 user 消息正文。

    - user_text 经 normalize_text 后不得为空，否则 ValueError（消息含 \"user_text\"）
    - label strip 后若为空，回退为 \"待分类文本\"
    - 返回：
      【{label}】
      {normalized_user_text}
    """
    # TODO: 实现 user 渲染
    raise NotImplementedError


def build_classification_messages(
    spec: ClassificationPrompt,
    user_text: str,
    *,
    user_label: str = "待分类文本",
) -> list[dict[str, str]]:
    """组装 OpenAI 风格 messages。

    返回恰好两条：
    1. {\"role\": \"system\", \"content\": render_system_prompt(spec)}
    2. {\"role\": \"user\", \"content\": render_user_prompt(user_text, label=user_label)}
    """
    # TODO: 实现 messages 组装
    raise NotImplementedError
