"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import csv
import io
import json
import re
from collections.abc import Callable, Sequence
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

CompleteFn = Callable[[list[dict[str, str]]], str]

SECTION_ROLE = "角色"
SECTION_TASK = "任务"
SECTION_CONSTRAINTS = "约束"
SECTION_OUTPUT_FORMAT = "输出格式"

DEFAULT_ROLE = "严谨的会议纪要助理，只依据原文提炼决议与行动项"
DEFAULT_TASK = "从用户提供的会议原文中抽取结构化纪要，输出单个 JSON 对象"
DEFAULT_CONSTRAINTS: tuple[str, ...] = (
    "只依据【会议原文】内容，不得臆造未出现的人名/日期/决议/待办",
    "原文没有的日期字段必须用 null，不要用空字符串代替 null",
    "priority 只能是 high / medium / low；原文未提及时默认 medium",
    "至少包含 1 条决议或 1 条行动项",
    "只输出一个 JSON 对象，不要解释、不要 Markdown 代码围栏",
)

CSV_FIELDS: tuple[str, ...] = ("owner", "task", "due_date", "priority")

Priority = Literal["high", "medium", "low"]


class ActionItem(BaseModel):
    """单条行动项。"""

    owner: str = Field(min_length=1)
    task: str = Field(min_length=1)
    due_date: str | None = None
    priority: Priority = "medium"

    @field_validator("owner", "task")
    @classmethod
    def strip_required(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("must not be blank")
        return s

    @field_validator("due_date")
    @classmethod
    def due_date_yyyy_mm_dd(cls, v: str | None) -> str | None:
        if v is None:
            return v
        s = v.strip()
        if not s:
            return None
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            raise ValueError("due_date must be YYYY-MM-DD")
        return s


class MeetingMinutes(BaseModel):
    """结构化会议纪要。"""

    title: str = Field(min_length=1)
    meeting_date: str | None = None
    attendees: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("must not be blank")
        return s

    @field_validator("meeting_date")
    @classmethod
    def meeting_date_yyyy_mm_dd(cls, v: str | None) -> str | None:
        if v is None:
            return v
        s = v.strip()
        if not s:
            return None
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            raise ValueError("meeting_date must be YYYY-MM-DD")
        return s

    @field_validator("attendees", "decisions")
    @classmethod
    def strip_list_items(cls, v: list[str]) -> list[str]:
        out: list[str] = []
        for item in v:
            s = item.strip()
            if s:
                out.append(s)
        return out

    @model_validator(mode="after")
    def require_substance(self) -> MeetingMinutes:
        if not self.decisions and not self.action_items:
            raise ValueError("need at least one decision or action item")
        return self


def _find_object_slice(s: str, start: int = 0) -> tuple[int, int] | None:
    i = s.find("{", start)
    if i < 0:
        return None
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
                return i, j + 1
    return None


def extract_json_object(text: str) -> str:
    if not text or not text.strip():
        raise ValueError("empty model output")

    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    candidates: list[str] = []
    if fence:
        candidates.append(fence.group(1))
    candidates.append(text)

    for block in candidates:
        sl = _find_object_slice(block, 0)
        if sl is not None:
            return block[sl[0] : sl[1]]
    raise ValueError("no JSON object found")


def schema_for_prompt(model: type[BaseModel] = MeetingMinutes) -> str:
    return json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2)


def join_sections(sections: Sequence[tuple[str, str]]) -> str:
    parts: list[str] = []
    for title, body in sections:
        t = title.strip()
        b = body.strip()
        if not t or not b:
            continue
        parts.append(f"【{t}】\n{b}")
    return "\n\n".join(parts)


def normalize_date(value: str | None) -> str | None:
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return None

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return raw

    m = re.fullmatch(r"(\d{4})/(\d{1,2})/(\d{1,2})", raw)
    if m:
        y, mo, d = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return f"{y:04d}-{mo:02d}-{d:02d}"

    m = re.fullmatch(r"(\d{4})年(\d{1,2})月(\d{1,2})日", raw)
    if m:
        y, mo, d = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return f"{y:04d}-{mo:02d}-{d:02d}"

    raise ValueError(f"invalid date: {value!r}")


def format_constraints(constraints: Sequence[str]) -> str:
    lines: list[str] = []
    for item in constraints:
        s = item.strip()
        if s:
            lines.append(f"- {s}")
    if not lines:
        raise ValueError("constraints")
    return "\n".join(lines)


def build_minutes_system_prompt(
    *,
    role: str = DEFAULT_ROLE,
    task: str = DEFAULT_TASK,
    constraints: Sequence[str] | None = None,
) -> str:
    if not role.strip():
        raise ValueError("role")
    if not task.strip():
        raise ValueError("task")
    cons = DEFAULT_CONSTRAINTS if constraints is None else constraints
    return join_sections(
        [
            (SECTION_ROLE, role.strip()),
            (SECTION_TASK, task.strip()),
            (SECTION_CONSTRAINTS, format_constraints(cons)),
            (
                SECTION_OUTPUT_FORMAT,
                "JSON Schema:\n" + schema_for_prompt(MeetingMinutes),
            ),
        ]
    )


def wrap_minutes_text(text: str) -> str:
    body = text.strip()
    if not body:
        raise ValueError("text")
    return f"【会议原文】\n{body}\n【会议原文结束】"


def build_minutes_messages(text: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": build_minutes_system_prompt()},
        {"role": "user", "content": wrap_minutes_text(text)},
    ]


def parse_minutes(raw: str) -> MeetingMinutes:
    try:
        obj = extract_json_object(raw)
        data: Any = json.loads(obj)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid json: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("validation failed: root must be object")

    if "meeting_date" in data:
        data = {**data, "meeting_date": normalize_date(data.get("meeting_date"))}

    items = data.get("action_items")
    if isinstance(items, list):
        normalized_items: list[Any] = []
        for item in items:
            if isinstance(item, dict) and "due_date" in item:
                normalized_items.append(
                    {**item, "due_date": normalize_date(item.get("due_date"))}
                )
            else:
                normalized_items.append(item)
        data = {**data, "action_items": normalized_items}

    try:
        return MeetingMinutes.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"validation failed: {e}") from e


def extract_minutes(text: str, complete_fn: CompleteFn) -> MeetingMinutes:
    if not text.strip():
        raise ValueError("text")
    messages = build_minutes_messages(text)
    raw = complete_fn(messages)
    return parse_minutes(raw)


def minutes_to_markdown(minutes: MeetingMinutes) -> str:
    date_text = minutes.meeting_date or "未注明"
    attendees_text = "、".join(minutes.attendees) if minutes.attendees else "未注明"

    lines: list[str] = [
        f"# {minutes.title}",
        "",
        f"- 日期：{date_text}",
        f"- 参会：{attendees_text}",
        "",
        "## 决议",
    ]
    if not minutes.decisions:
        lines.append("（无）")
    else:
        for i, d in enumerate(minutes.decisions, start=1):
            lines.append(f"{i}. {d}")

    lines.extend(["", "## Action Items"])
    if not minutes.action_items:
        lines.append("（无）")
    else:
        for item in minutes.action_items:
            due = item.due_date or "未定"
            lines.append(f"- [{item.priority}] {item.owner}：{item.task}（截止：{due}）")

    lines.append("")
    return "\n".join(lines)


def action_items_to_csv(items: Sequence[ActionItem]) -> str:
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=list(CSV_FIELDS), lineterminator="\n")
    writer.writeheader()
    for item in items:
        row = item.model_dump(mode="json")
        writer.writerow(
            {
                "owner": row.get("owner") or "",
                "task": row.get("task") or "",
                "due_date": row.get("due_date") or "",
                "priority": row.get("priority") or "",
            }
        )
    return buf.getvalue()


def minutes_to_json(minutes: MeetingMinutes, *, indent: int | None = 2) -> str:
    return json.dumps(minutes.model_dump(mode="json"), ensure_ascii=False, indent=indent)


def minutes_summary(minutes: MeetingMinutes) -> dict[str, int | list[str]]:
    owners: list[str] = []
    seen: set[str] = set()
    for item in minutes.action_items:
        if item.owner not in seen:
            seen.add(item.owner)
            owners.append(item.owner)
    return {
        "decisions": len(minutes.decisions),
        "action_items": len(minutes.action_items),
        "attendees": len(minutes.attendees),
        "owners": owners,
    }
