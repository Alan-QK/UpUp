"""Day 27 练习：校验失败重试（repair loop）。

Schema / 抽取 / 校验函数已给出（承接 Day 26），请完成 TODO。
需要：pydantic>=2（python3 -m pip install --user 'pydantic>=2'）
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ValidationError

# ---------------------------------------------------------------------------
# 以下 Schema / 解析工具已给出 —— 练习中请勿修改
# ---------------------------------------------------------------------------


class Priority(str, Enum):
    """任务优先级。"""

    low = "low"
    medium = "medium"
    high = "high"


class TaskItem(BaseModel):
    """单条任务。"""

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    priority: Priority
    tags: list[str] = Field(default_factory=list)
    estimate_hours: float | None = Field(default=None, ge=0)


class TaskBatch(BaseModel):
    """一批任务。"""

    tasks: list[TaskItem] = Field(min_length=1)


def _find_object_slice(s: str, start: int = 0) -> tuple[int, int] | None:
    """从 start 起找第一个完整 `{...}` 切片（尊重字符串内花括号）。"""
    i = s.find("{", start)
    if i < 0:
        return None
    depth = 0
    in_str = False
    escape = False
    for j in range(i, len(s)):
        ch = s[j]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i, j + 1
    return None


def extract_json_object(text: str) -> str:
    """从模型回复抽出第一个完整 JSON 对象字符串。"""
    if not text or not text.strip():
        raise ValueError("empty model output")

    fence_start = text.find("```")
    search_from = 0
    if fence_start >= 0:
        after = text.find("\n", fence_start)
        if after < 0:
            after = fence_start + 3
        fence_end = text.find("```", after)
        if fence_end > after:
            inner = text[after:fence_end]
            sliced = _find_object_slice(inner)
            if sliced is not None:
                a, b = sliced
                return inner[a:b]
            search_from = 0

    sliced = _find_object_slice(text, search_from)
    if sliced is None:
        raise ValueError("no json object found")
    a, b = sliced
    return text[a:b]


def validation_error_summary(exc: ValidationError) -> list[str]:
    """ValidationError → 可读摘要列表。"""
    lines: list[str] = []
    for err in exc.errors():
        loc = "/".join(str(x) for x in err.get("loc", ()))
        msg = str(err.get("msg", ""))
        lines.append(f"{loc}: {msg}" if loc else msg)
    return lines


def parse_task_batch(raw: str) -> TaskBatch:
    """extract → json.loads → model_validate。"""
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


# ---------------------------------------------------------------------------
# 以下为今日要完成的 repair loop
# ---------------------------------------------------------------------------

FAILURE_EXTRACT = "extract"
FAILURE_JSON = "json"
FAILURE_VALIDATION = "validation"
FAILURE_OTHER = "other"

ALLOWED_FAILURE_KINDS = frozenset(
    {FAILURE_EXTRACT, FAILURE_JSON, FAILURE_VALIDATION, FAILURE_OTHER}
)


@dataclass(frozen=True)
class AttemptRecord:
    """单次模型调用记录。"""

    attempt: int  # 从 1 起，含首次
    raw: str
    ok: bool
    error: str | None = None
    failure_kind: str | None = None


@dataclass(frozen=True)
class RepairResult:
    """repair loop 总结果。"""

    batch: TaskBatch | None
    attempts: tuple[AttemptRecord, ...]
    repaired: bool  # 至少经历过一次失败后才成功
    exhausted: bool  # 用尽次数仍失败


def classify_failure(exc: BaseException) -> str:
    """根据异常消息粗分失败类型。

    规则（按顺序匹配，返回常量字符串）：
    - 消息含 \"empty\" 或 \"no json object\" → extract
    - 消息含 \"invalid json\" 或 \"json\"（且非 validation）→ json
      更稳妥：含 \"invalid json\" → json；否则若含 \"validation failed\" → validation
    - 含 \"validation failed\" → validation
    - 其他 → other

    具体以测试为准：优先匹配 validation failed，再 invalid json / empty / no json object。
    """
    # TODO: 实现失败分类
    raise NotImplementedError


def build_repair_user_message(
    error_text: str,
    *,
    failure_kind: str,
    repair_index: int,
    max_repairs: int,
) -> str:
    """构造发给模型的修复指令（user 角色正文）。

    必须满足：
    - 正文包含 error_text（strip 后非空；若传入为空 → ValueError 含 \"error\"）
    - failure_kind 必须属于 ALLOWED_FAILURE_KINDS，否则 ValueError 含 \"kind\"
    - repair_index 从 1 起；须 1 <= repair_index <= max_repairs，否则 ValueError 含 \"repair\"
    - max_repairs >= 1，否则 ValueError 含 \"max_repairs\"
    - 正文必须包含字面量：\"只输出\" 以及 \"JSON\"
    - 正文必须包含 \"修复第\" 与 f\"{repair_index}/{max_repairs}\"
    - 若 failure_kind == validation：正文还需包含 \"字段\"
    - 若 failure_kind == extract：正文还需包含 \"完整\"
    - 若 failure_kind == json：正文还需包含 \"语法\"
    """
    # TODO: 实现修复 user 消息
    raise NotImplementedError


def append_repair_turn(
    messages: list[dict[str, str]],
    *,
    assistant_raw: str,
    repair_user: str,
) -> list[dict[str, str]]:
    """在消息列表末尾追加一轮失败对话，返回**新列表**（不要原地改传入 list）。

    追加顺序：
    1. {\"role\": \"assistant\", \"content\": assistant_raw}
    2. {\"role\": \"user\", \"content\": repair_user}

    - assistant_raw / repair_user 任一 strip 为空 → ValueError（消息含 \"assistant\" 或 \"user\"）
    """
    # TODO: 追加 assistant + user
    raise NotImplementedError


def run_repair_loop(
    *,
    llm: Callable[[list[dict[str, str]]], str],
    initial_messages: list[dict[str, str]],
    max_repairs: int = 3,
) -> RepairResult:
    """执行 generate → parse →（失败则 repair）循环。

    约定：
    - max_repairs < 0 → ValueError（含 \"max_repairs\"）；允许 0（表示不允许修复，只试 1 次）
    - initial_messages 不能为空，否则 ValueError（含 \"messages\"）
    - 每次调用 llm 前传入**当前** messages 的浅拷贝 list（避免 llm 侧修改污染）
    - 首次调用不算 repair；失败后 repair_index 从 1 计到 max_repairs
    - 成功：batch 非空；若 attempts 里曾有 ok=False，则 repaired=True，否则 repaired=False
    - 用尽仍失败：batch=None，exhausted=True，repaired=False
    - 每次 AttemptRecord.attempt 从 1 连续编号
    - parse 失败时：error=str(exc)，failure_kind=classify_failure(exc)
    - 修复 user 消息用 build_repair_user_message；随后 append_repair_turn
    """
    # TODO: 实现 repair loop
    raise NotImplementedError


# 占位，避免未使用导入告警
_ = (Any, json)
