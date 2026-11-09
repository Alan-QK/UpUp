"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field, ValidationError


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

    attempt: int
    raw: str
    ok: bool
    error: str | None = None
    failure_kind: str | None = None


@dataclass(frozen=True)
class RepairResult:
    """repair loop 总结果。"""

    batch: TaskBatch | None
    attempts: tuple[AttemptRecord, ...]
    repaired: bool
    exhausted: bool


def classify_failure(exc: BaseException) -> str:
    """根据异常消息粗分失败类型。"""
    msg = str(exc).lower()
    if "validation failed" in msg:
        return FAILURE_VALIDATION
    if "invalid json" in msg:
        return FAILURE_JSON
    if "empty" in msg or "no json object" in msg:
        return FAILURE_EXTRACT
    if "json" in msg and "validation" not in msg:
        return FAILURE_JSON
    return FAILURE_OTHER


def build_repair_user_message(
    error_text: str,
    *,
    failure_kind: str,
    repair_index: int,
    max_repairs: int,
) -> str:
    """构造发给模型的修复指令（user 角色正文）。"""
    if max_repairs < 1:
        raise ValueError("max_repairs must be >= 1")
    cleaned = error_text.strip()
    if not cleaned:
        raise ValueError("error text is empty")
    if failure_kind not in ALLOWED_FAILURE_KINDS:
        raise ValueError(f"unknown kind: {failure_kind}")
    if repair_index < 1 or repair_index > max_repairs:
        raise ValueError("repair index out of range")

    hint = "请根据错误修正后只输出一个 JSON 对象，不要解释。"
    if failure_kind == FAILURE_VALIDATION:
        hint = "请按下列字段错误逐项改正，只输出修复后的 JSON，不要解释。"
    elif failure_kind == FAILURE_EXTRACT:
        hint = "请输出一个完整的 JSON 对象（含花括号），只输出 JSON，不要解释。"
    elif failure_kind == FAILURE_JSON:
        hint = "请检查 JSON 语法（逗号/引号/括号），只输出修复后的 JSON，不要解释。"

    return (
        f"上次输出未通过校验（修复第 {repair_index}/{max_repairs} 次）。\n"
        f"错误：\n{cleaned}\n\n"
        f"{hint}"
    )


def append_repair_turn(
    messages: list[dict[str, str]],
    *,
    assistant_raw: str,
    repair_user: str,
) -> list[dict[str, str]]:
    """在消息列表末尾追加一轮失败对话，返回新列表。"""
    if not assistant_raw.strip():
        raise ValueError("assistant raw is empty")
    if not repair_user.strip():
        raise ValueError("user repair message is empty")
    return [
        *messages,
        {"role": "assistant", "content": assistant_raw},
        {"role": "user", "content": repair_user},
    ]


def run_repair_loop(
    *,
    llm: Callable[[list[dict[str, str]]], str],
    initial_messages: list[dict[str, str]],
    max_repairs: int = 3,
) -> RepairResult:
    """执行 generate → parse →（失败则 repair）循环。"""
    if max_repairs < 0:
        raise ValueError("max_repairs must be >= 0")
    if not initial_messages:
        raise ValueError("messages must not be empty")

    messages: list[dict[str, str]] = [dict(m) for m in initial_messages]
    attempts: list[AttemptRecord] = []
    had_failure = False

    total_allowed = 1 + max_repairs
    for attempt in range(1, total_allowed + 1):
        raw = llm(list(messages))
        try:
            batch = parse_task_batch(raw)
        except Exception as exc:  # noqa: BLE001 - 统一收口到轨迹
            kind = classify_failure(exc)
            attempts.append(
                AttemptRecord(
                    attempt=attempt,
                    raw=raw,
                    ok=False,
                    error=str(exc),
                    failure_kind=kind,
                )
            )
            had_failure = True
            repairs_used = attempt - 1
            if repairs_used >= max_repairs:
                return RepairResult(
                    batch=None,
                    attempts=tuple(attempts),
                    repaired=False,
                    exhausted=True,
                )
            repair_index = repairs_used + 1
            repair_user = build_repair_user_message(
                str(exc),
                failure_kind=kind,
                repair_index=repair_index,
                max_repairs=max_repairs,
            )
            messages = append_repair_turn(
                messages,
                assistant_raw=raw,
                repair_user=repair_user,
            )
            continue

        attempts.append(
            AttemptRecord(
                attempt=attempt,
                raw=raw,
                ok=True,
                error=None,
                failure_kind=None,
            )
        )
        return RepairResult(
            batch=batch,
            attempts=tuple(attempts),
            repaired=had_failure,
            exhausted=False,
        )

    return RepairResult(
        batch=None,
        attempts=tuple(attempts),
        repaired=False,
        exhausted=True,
    )
