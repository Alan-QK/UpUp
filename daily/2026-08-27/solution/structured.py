"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import json
from enum import Enum

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
    """去掉首尾空白，并把内部连续空白（含换行）压成单个空格。"""
    return " ".join(text.split())


def _find_object_slice(s: str, start: int = 0) -> str:
    """从 s[start:] 起用深度扫描取出第一个完整 JSON 对象。"""
    i = s.find("{", start)
    if i < 0:
        raise ValueError("no JSON object found")

    depth = 0
    in_string = False
    escape = False
    for j in range(i, len(s)):
        ch = s[j]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[i : j + 1]
    raise ValueError("unbalanced JSON braces")


def extract_json_object(text: str) -> str:
    """从模型回复抽出第一个完整 JSON 对象字符串。"""
    if not text or not text.strip():
        raise ValueError("empty text")

    # 围栏优先：```json ... ``` 或 ``` ... ```
    fence_start = text.find("```")
    if fence_start >= 0:
        after = text[fence_start + 3 :]
        # 可选语言标记
        nl = after.find("\n")
        if nl >= 0:
            body = after[nl + 1 :]
        else:
            body = after
        fence_end = body.find("```")
        if fence_end >= 0:
            body = body[:fence_end]
        return _find_object_slice(body)

    return _find_object_slice(text)


def schema_for_prompt(model: type[BaseModel]) -> str:
    """把 pydantic 模型的 JSON Schema 格式化为可放入 Prompt 的文本。"""
    return json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2)


def format_constraints(constraints: list[str] | tuple[str, ...]) -> str:
    """把约束格式化为 Markdown 无序列表。"""
    lines: list[str] = []
    for item in constraints:
        normalized = normalize_text(item)
        if normalized:
            lines.append(f"- {normalized}")
    return "\n".join(lines)


def join_sections(sections: list[tuple[str, str]]) -> str:
    """按列表拼装【标题】章节。"""
    parts: list[str] = []
    for title, body in sections:
        t = title.strip() if title else ""
        b = body.strip() if body else ""
        if not t or not b:
            continue
        parts.append(f"【{t}】\n{b}")
    return "\n\n".join(parts)


def build_structured_system_prompt(
    *,
    role: str = DEFAULT_ROLE,
    task: str = DEFAULT_TASK,
    constraints: list[str] | tuple[str, ...] | None = None,
    schema_model: type[BaseModel] = TaskBatch,
) -> str:
    """组装 system Prompt。"""
    if not normalize_text(role):
        raise ValueError("role is empty")
    if not normalize_text(task):
        raise ValueError("task is empty")

    raw_constraints = DEFAULT_CONSTRAINTS if constraints is None else constraints
    constraint_text = format_constraints(raw_constraints)
    if not constraint_text:
        raise ValueError("constraints is empty")

    output_format = "JSON Schema:\n" + schema_for_prompt(schema_model)
    return join_sections(
        [
            (SECTION_ROLE, normalize_text(role)),
            (SECTION_TASK, normalize_text(task)),
            (SECTION_CONSTRAINTS, constraint_text),
            (SECTION_OUTPUT_FORMAT, output_format),
        ]
    )


def build_structured_messages(
    user_text: str,
    *,
    role: str = DEFAULT_ROLE,
    task: str = DEFAULT_TASK,
    constraints: list[str] | tuple[str, ...] | None = None,
    schema_model: type[BaseModel] = TaskBatch,
) -> list[dict[str, str]]:
    """生成 system + user messages。"""
    if not user_text.strip():
        raise ValueError("user text is empty")
    system = build_structured_system_prompt(
        role=role,
        task=task,
        constraints=constraints,
        schema_model=schema_model,
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_text.strip()},
    ]


def validation_error_summary(exc: ValidationError) -> list[str]:
    """把 ValidationError 转成可读摘要列表。"""
    lines: list[str] = []
    for err in exc.errors():
        loc_parts = [str(p) for p in err.get("loc", ())]
        path = "/".join(loc_parts)
        msg = err.get("msg", "")
        lines.append(f"{path}: {msg}")
    return lines


def parse_task_batch(raw: str) -> TaskBatch:
    """从模型原始文本解析并校验为 TaskBatch。"""
    obj_text = extract_json_object(raw)
    try:
        data = json.loads(obj_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid json: {exc}") from exc
    try:
        return TaskBatch.model_validate(data)
    except ValidationError as exc:
        summary = " | ".join(validation_error_summary(exc))
        raise ValueError(f"validation failed: {summary}") from exc


def _format_hours(hours: float) -> str:
    """去掉无意义尾随 0：1.0→1，2.5→2.5。"""
    if hours == int(hours):
        return str(int(hours))
    return str(hours)


def tasks_to_markdown(batch: TaskBatch) -> str:
    """渲染 Markdown 列表。"""
    lines: list[str] = []
    for item in batch.tasks:
        line = f"- [{item.id}] {item.title} ({item.priority.value})"
        if item.tags:
            line += f" · tags: {', '.join(item.tags)}"
        if item.estimate_hours is not None:
            line += f" · ~{_format_hours(item.estimate_hours)}h"
        lines.append(line)
    return "\n".join(lines)


def parse_and_render(raw: str) -> tuple[TaskBatch, str]:
    """便利函数：解析校验 + 渲染。"""
    batch = parse_task_batch(raw)
    return batch, tasks_to_markdown(batch)
