"""Day 26 练习：JSON 结构化输出（pydantic 校验）。

请完成 TODO，使 tests/ 全部通过。
需要：pydantic>=2（python3 -m pip install --user 'pydantic>=2'）
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ValidationError

SECTION_ROLE = "角色"
SECTION_TASK = "任务"
SECTION_CONSTRAINTS = "约束"
SECTION_OUTPUT_FORMAT = "输出格式"

DEFAULT_ROLE = "严谨的项目助理，只输出符合 schema 的 JSON"
DEFAULT_TASK = "把用户描述整理成任务清单 JSON"
DEFAULT_CONSTRAINTS: tuple[str, ...] = (
    "只依据用户描述，不得臆造未提及的任务",
    "priority 只能是 low / medium / high",
    "estimate_hours 若存在必须 >= 0",
    "只输出一个 JSON 对象，不要解释、不要 Markdown 代码围栏",
)


class Priority(str, Enum):
    """任务优先级。"""

    low = "low"
    medium = "medium"
    high = "high"


class TaskItem(BaseModel):
    """单条任务（模型输出契约）。"""

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    priority: Priority
    tags: list[str] = Field(default_factory=list)
    estimate_hours: float | None = Field(default=None, ge=0)


class TaskBatch(BaseModel):
    """一批任务。"""

    tasks: list[TaskItem] = Field(min_length=1)


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白（含换行）压成单个空格。

    例：\"  你好\\n\\n世界  \" → \"你好 世界\"
    """
    # TODO: 实现空白规范化
    raise NotImplementedError


def extract_json_object(text: str) -> str:
    """从模型回复抽出第一个完整 JSON 对象字符串。

    - 允许前后废话；若存在 ``` / ```json 围栏，优先取围栏内对象
    - 用括号深度扫描（注意字符串内的花括号），不要用贪婪正则硬切
    - 找不到或括号不配平 → ValueError
    - 空文本 → ValueError（消息含 \"empty\"）
    """
    # TODO: 实现 JSON 抽取
    raise NotImplementedError


def schema_for_prompt(model: type[BaseModel]) -> str:
    """把 pydantic 模型的 JSON Schema 格式化为可放入 Prompt 的文本。

    - 使用 model.model_json_schema()
    - 返回 indent=2、ensure_ascii=False 的 JSON 字符串
    """
    # TODO: 导出 schema 文本
    raise NotImplementedError


def format_constraints(constraints: list[str] | tuple[str, ...]) -> str:
    """把约束格式化为 Markdown 无序列表（跳过空项；每项先 normalize_text）。"""
    # TODO: 实现约束列表格式化
    raise NotImplementedError


def join_sections(sections: list[tuple[str, str]]) -> str:
    """按列表拼装【标题】章节；标题或正文为空则整节省略；章节间用空行分隔。"""
    # TODO: 实现章节拼接
    raise NotImplementedError


def build_structured_system_prompt(
    *,
    role: str = DEFAULT_ROLE,
    task: str = DEFAULT_TASK,
    constraints: list[str] | tuple[str, ...] | None = None,
    schema_model: type[BaseModel] = TaskBatch,
) -> str:
    """组装 system Prompt。

    章节顺序：角色 → 任务 → 约束 → 输出格式
    - role / task 空 → ValueError（消息含字段名）
    - constraints 为 None 时用 DEFAULT_CONSTRAINTS；有效约束为空 → ValueError（含 \"constraints\"）
    - 输出格式章节正文 = \"JSON Schema:\\n\" + schema_for_prompt(schema_model)
    """
    # TODO: 组装 system prompt
    raise NotImplementedError


def build_structured_messages(
    user_text: str,
    *,
    role: str = DEFAULT_ROLE,
    task: str = DEFAULT_TASK,
    constraints: list[str] | tuple[str, ...] | None = None,
    schema_model: type[BaseModel] = TaskBatch,
) -> list[dict[str, str]]:
    """生成 [{\"role\":\"system\",...}, {\"role\":\"user\",...}]。

    - user_text strip 后为空 → ValueError（含 \"user\"）
    """
    # TODO: 组装 messages
    raise NotImplementedError


def validation_error_summary(exc: ValidationError) -> list[str]:
    """把 ValidationError 转成可读摘要列表。

    每条格式：\"/\".join(loc) + \": \" + msg
    - loc 中的非 str/int 元素转成 str
    - 保持 errors() 原始顺序
    """
    # TODO: 实现错误摘要
    raise NotImplementedError


def parse_task_batch(raw: str) -> TaskBatch:
    """从模型原始文本解析并校验为 TaskBatch。

    流程：extract_json_object → json.loads → TaskBatch.model_validate
    - json.loads 失败 → ValueError（含 \"json\"）
    - ValidationError → 重新抛出 ValueError，消息为：
      \"validation failed: \" + \" | \".join(validation_error_summary(exc))
    """
    # TODO: 抽取 + 校验
    raise NotImplementedError


def tasks_to_markdown(batch: TaskBatch) -> str:
    """渲染 Markdown 列表。

    每条：\"- [id] title (priority)\"；若有 tags 则追加 \" · tags: a, b\"；
    若 estimate_hours 非 None 则追加 \" · ~Xh\"（X 去掉无意义的尾随 0，如 1.0→1，2.5→2.5）
    """
    # TODO: 实现 Markdown 渲染
    raise NotImplementedError


def parse_and_render(raw: str) -> tuple[TaskBatch, str]:
    """便利函数：解析校验 + 渲染。返回 (batch, markdown)。"""
    # TODO: 组合 parse_task_batch + tasks_to_markdown
    raise NotImplementedError


# 练习实现时会用到
_ = (Any, json, ValidationError)
