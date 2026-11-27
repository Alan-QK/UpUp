"""Day 29 练习：批量信息抽取（文本 → 字段 → JSON/CSV）。

Contact Schema 与 JSON 抽取辅助已给出 —— 请勿修改。
请完成 TODO，使 tests/ 全部通过。
需要：pydantic>=2
"""

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


# ---------------------------------------------------------------------------
# Schema（已给出 —— 勿改）
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# JSON 抽取辅助（已给出 —— 勿改）
# ---------------------------------------------------------------------------


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
    """导出 pydantic JSON Schema 文本（indent=2）。"""
    return json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2)


def join_sections(sections: Sequence[tuple[str, str]]) -> str:
    """按列表拼装【标题】章节；标题或正文为空则整节省略。"""
    parts: list[str] = []
    for title, body in sections:
        t = title.strip()
        b = body.strip()
        if not t or not b:
            continue
        parts.append(f"【{t}】\n{b}")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# 请你实现
# ---------------------------------------------------------------------------


def normalize_phone(phone: str | None) -> str | None:
    """规范化电话：保留数字与开头的单个 +；空/纯空白 → None。

    例：
    - \"010-1234 5678\" → \"01012345678\"
    - \"+86 138-0000-1111\" → \"+8613800001111\"
    - \"  \" → None
    - None → None
    """
    # TODO
    raise NotImplementedError


def format_constraints(constraints: Sequence[str]) -> str:
    """Markdown 无序列表；跳过空项；每项 strip。有效项为空 → ValueError(\"constraints\")。"""
    # TODO
    raise NotImplementedError


def build_extract_system_prompt(
    *,
    role: str = DEFAULT_ROLE,
    task: str = DEFAULT_TASK,
    constraints: Sequence[str] | None = None,
) -> str:
    """组装 system Prompt。

    章节顺序：角色 → 任务 → 约束 → 输出格式
    - role / task 空 → ValueError（消息含字段名）
    - constraints 为 None 时用 DEFAULT_CONSTRAINTS
    - 输出格式正文 = \"JSON Schema:\\n\" + schema_for_prompt(Contact)
    """
    # TODO
    raise NotImplementedError


def wrap_source_text(text: str) -> str:
    """用边界标记包裹原文。

    格式（注意换行）：
        【原文】
        {text.strip()}
        【原文结束】

    text 全空白 → ValueError（含 \"text\"）
    """
    # TODO
    raise NotImplementedError


def build_extract_messages(text: str) -> list[dict[str, str]]:
    """返回 [system, user] 两条消息。"""
    # TODO: system=build_extract_system_prompt()；user=wrap_source_text(text)
    raise NotImplementedError


def parse_contact(raw: str) -> Contact:
    """从模型原始回复解析 Contact。

    - extract_json_object → json.loads → Contact.model_validate
    - 若存在 phone 字段，先经 normalize_phone 再校验
      （可在 dict 层面改 phone，再 model_validate）
    - ValidationError → 包装为 ValueError(\"validation failed: ...\")
    - JSON 解码失败 → ValueError（含 \"invalid json\"）
    """
    # TODO
    raise NotImplementedError


def extract_one(source_id: str, text: str, complete_fn: CompleteFn) -> ExtractResult:
    """抽取单条。

    - source_id 空/空白 → ExtractResult(ok=False, error 含 \"source_id\")，不调用模型
    - 其余异常（含 parse / complete_fn）→ ok=False，error=异常消息字符串
    - 成功 → ok=True, contact=...
    """
    # TODO
    raise NotImplementedError


def extract_batch(
    items: Sequence[tuple[str, str]],
    complete_fn: CompleteFn,
) -> list[ExtractResult]:
    """按顺序对 (source_id, text) 逐条 extract_one，返回等长结果列表。"""
    # TODO
    raise NotImplementedError


def successful_contacts(results: Sequence[ExtractResult]) -> list[Contact]:
    """按原顺序收集 ok 且 contact 非空的记录。"""
    # TODO
    raise NotImplementedError


def contacts_to_json(contacts: Sequence[Contact], *, indent: int | None = 2) -> str:
    """导出 JSON 数组字符串（ensure_ascii=False）。

    每条用 contact.model_dump(mode=\"json\")。
    """
    # TODO
    raise NotImplementedError


def contacts_to_csv(contacts: Sequence[Contact]) -> str:
    """导出 CSV 文本（含表头）。

    - 列顺序固定为 CSV_FIELDS
    - tags 用英文分号 \"\";\"\" 拼接
    - 空值写空字符串
    - 使用 csv 模块（Dialect 默认即可），newline 用 \\n
    - 无数据时仍要有表头行
    """
    # TODO
    raise NotImplementedError


def batch_summary(results: Sequence[ExtractResult]) -> dict[str, int]:
    """返回 {\"total\", \"ok\", \"failed\"}。"""
    # TODO
    raise NotImplementedError
