"""Day 21 练习：Prompt 结构拆解（模板函数库）。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库。
"""

from __future__ import annotations

from dataclasses import dataclass, field


SECTION_ROLE = "角色"
SECTION_TASK = "任务"
SECTION_CONSTRAINTS = "约束"
SECTION_OUTPUT_FORMAT = "输出格式"
SECTION_CONTEXT = "上下文"

# 固定章节顺序（渲染时按此顺序；空章节跳过）
SECTION_ORDER = (
    SECTION_ROLE,
    SECTION_TASK,
    SECTION_CONSTRAINTS,
    SECTION_OUTPUT_FORMAT,
    SECTION_CONTEXT,
)


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白（含换行）压成单个空格。

    例：\"  你好\\n\\n世界  \" → \"你好 世界\"
    """
    # TODO: 实现空白规范化
    raise NotImplementedError


def format_constraints(constraints: list[str]) -> str:
    """把约束列表格式化为 Markdown 无序列表。

    规则：
    - 先对每一项 normalize_text；跳过规范化后为空的项
    - 每行形如：\"- {item}\"
    - 多项之间用单个换行连接
    - 若有效项为空，返回 \"\"
    """
    # TODO: 实现约束列表格式化
    raise NotImplementedError


def join_sections(sections: list[tuple[str, str]]) -> str:
    """按给定列表拼装章节。

    每个元素是 (标题, 正文)。
    - 标题、正文都先 normalize 思路：标题 strip；正文若 strip 后为空则**整章节跳过**
    - 保留的章节形如：
      【标题】
      正文
    - 章节之间用两个换行（即中间有一空行）分隔
    - 若全部跳过，返回 \"\"
    """
    # TODO: 实现章节拼装
    raise NotImplementedError


@dataclass
class PromptSpec:
    """结构化 Prompt 规格。"""

    role: str
    task: str
    output_format: str
    constraints: list[str] = field(default_factory=list)
    context: str | None = None


def validate_spec(spec: PromptSpec) -> None:
    """校验必填字段。

    - role / task / output_format：normalize 后不得为空，否则 ValueError
      消息分别包含：\"role\" / \"task\" / \"output_format\"
    - constraints：必须是 list（允许空列表）；不做「非空」强制
    - context：None 或 str 均可；若是 str 且 normalize 后为空，视为「无上下文」
      （校验阶段不报错，渲染时跳过）
    """
    # TODO: 实现校验
    raise NotImplementedError


def render_system_prompt(spec: PromptSpec) -> str:
    """把 PromptSpec 渲染为 system 文本。

    步骤：
    1. validate_spec(spec)
    2. 按 SECTION_ORDER 组装：
       - 角色 ← spec.role
       - 任务 ← spec.task
       - 约束 ← format_constraints(spec.constraints)（空则跳过整节）
       - 输出格式 ← spec.output_format
       - 上下文 ← spec.context（None 或空白则跳过）
    3. 返回 join_sections(...)
    """
    # TODO: 实现 system 渲染
    raise NotImplementedError


def render_user_prompt(user_input: str, *, label: str = "用户输入") -> str:
    """渲染 user 消息正文。

    - user_input 经 normalize_text 后不得为空，否则 ValueError（消息含 \"user_input\"）
    - label strip 后若为空，回退为 \"用户输入\"
    - 返回：
      【{label}】
      {normalized_user_input}
    """
    # TODO: 实现 user 渲染
    raise NotImplementedError


def build_chat_messages(
    spec: PromptSpec,
    user_input: str,
    *,
    user_label: str = "用户输入",
) -> list[dict[str, str]]:
    """组装 OpenAI 风格 messages。

    返回恰好两条：
    1. {\"role\": \"system\", \"content\": render_system_prompt(spec)}
    2. {\"role\": \"user\", \"content\": render_user_prompt(user_input, label=user_label)}
    """
    # TODO: 实现 messages 组装
    raise NotImplementedError
