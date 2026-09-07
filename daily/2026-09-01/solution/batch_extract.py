"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import csv
import io
import json
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

CompleteFn = Callable[[list[dict[str, str]]], str]

SECTION_ROLE = "角色"
SECTION_TASK = "任务"
SECTION_CONSTRAINTS = "约束"
SECTION_OUTPUT_FORMAT = "输出格式"

DEFAULT_ROLE = "严谨的信息抽取助理，只依据原文填写字段"
DEFAULT_TASK = "从用户提供的原文中抽取联系人信息，输出单个 JSON 对象"
DEFAULT_CONSTRAINTS: tuple[str, ...] = (
    "只依据【原文】内容，不得臆造未出现的姓名/邮箱/电话/公司",
    "原文没有的字段必须用 null，不要用空字符串代替 null",
    "tags 只收录原文明确提到的标签；没有则 []",
    "只输出一个 JSON 对象，不要解释、不要 Markdown 代码围栏",
)

CSV_FIELDS: tuple[str, ...] = (
    "name",
    "email",
    "phone",
    "company",
    "title",
    "tags",
)


class Contact(BaseModel):
    """单条联系人抽取结果。"""

    name: str = Field(min_length=1)
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    title: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("email")
    @classmethod
    def email_must_have_at(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if "@" not in v:
            raise ValueError("email must contain @")
        return v.strip()

    @field_validator("name", "company", "title")
    @classmethod
    def strip_nonempty(cls, v: str | None) -> str | None:
        if v is None:
            return v
        s = v.strip()
        if not s:
            raise ValueError("must not be blank")
        return s


@dataclass(frozen=True)
class ExtractResult:
    """单条抽取结果（成功或失败）。"""

    source_id: str
    ok: bool
    contact: Contact | None = None
    error: str | None = None


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
    """从模型回复抽出第一个完整 JSON 对象字符串。"""
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


def schema_for_prompt(model: type[BaseModel] = Contact) -> str:
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


def normalize_phone(phone: str | None) -> str | None:
    if phone is None:
        return None
    raw = phone.strip()
    if not raw:
        return None
    has_plus = raw.startswith("+")
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return None
    return f"+{digits}" if has_plus else digits


def format_constraints(constraints: Sequence[str]) -> str:
    lines: list[str] = []
    for item in constraints:
        s = item.strip()
        if s:
            lines.append(f"- {s}")
    if not lines:
        raise ValueError("constraints")
    return "\n".join(lines)


def build_extract_system_prompt(
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
                "JSON Schema:\n" + schema_for_prompt(Contact),
            ),
        ]
    )


def wrap_source_text(text: str) -> str:
    body = text.strip()
    if not body:
        raise ValueError("text")
    return f"【原文】\n{body}\n【原文结束】"


def build_extract_messages(text: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": build_extract_system_prompt()},
        {"role": "user", "content": wrap_source_text(text)},
    ]


def parse_contact(raw: str) -> Contact:
    try:
        obj = extract_json_object(raw)
        data: Any = json.loads(obj)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid json: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("validation failed: root must be object")
    if "phone" in data:
        data = {**data, "phone": normalize_phone(data.get("phone"))}
    try:
        return Contact.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"validation failed: {e}") from e


def extract_one(source_id: str, text: str, complete_fn: CompleteFn) -> ExtractResult:
    sid = source_id.strip() if source_id else ""
    if not sid:
        return ExtractResult(source_id=source_id, ok=False, error="source_id is required")
    try:
        messages = build_extract_messages(text)
        raw = complete_fn(messages)
        contact = parse_contact(raw)
        return ExtractResult(source_id=sid, ok=True, contact=contact)
    except Exception as e:
        return ExtractResult(source_id=sid, ok=False, error=str(e))


def extract_batch(
    items: Sequence[tuple[str, str]],
    complete_fn: CompleteFn,
) -> list[ExtractResult]:
    return [extract_one(sid, text, complete_fn) for sid, text in items]


def successful_contacts(results: Sequence[ExtractResult]) -> list[Contact]:
    return [r.contact for r in results if r.ok and r.contact is not None]


def contacts_to_json(contacts: Sequence[Contact], *, indent: int | None = 2) -> str:
    payload = [c.model_dump(mode="json") for c in contacts]
    return json.dumps(payload, ensure_ascii=False, indent=indent)


def contacts_to_csv(contacts: Sequence[Contact]) -> str:
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=list(CSV_FIELDS), lineterminator="\n")
    writer.writeheader()
    for c in contacts:
        row = c.model_dump(mode="json")
        writer.writerow(
            {
                "name": row.get("name") or "",
                "email": row.get("email") or "",
                "phone": row.get("phone") or "",
                "company": row.get("company") or "",
                "title": row.get("title") or "",
                "tags": ";".join(row.get("tags") or []),
            }
        )
    return buf.getvalue()


def batch_summary(results: Sequence[ExtractResult]) -> dict[str, int]:
    ok = sum(1 for r in results if r.ok)
    total = len(results)
    return {"total": total, "ok": ok, "failed": total - ok}
