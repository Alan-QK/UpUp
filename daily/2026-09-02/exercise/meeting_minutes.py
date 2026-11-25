"""Day 30 练习：会议纪要结构化（决议 + action items）。

ActionItem / MeetingMinutes Schema 与 JSON 抽取辅助已给出 —— 请勿修改。
请完成 TODO，使 tests/ 全部通过。
需要：pydantic>=2
"""

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


# ---------------------------------------------------------------------------
# Schema（已给出 —— 勿改）
# ---------------------------------------------------------------------------


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


def schema_for_prompt(model: type[BaseModel] = MeetingMinutes) -> str:
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


def normalize_date(value: str | None) -> str | None:
    """把常见日期写法规范成 YYYY-MM-DD；空 → None。

    支持：
    - 已是 YYYY-MM-DD
    - YYYY/M/D 或 YYYY/MM/DD
    - YYYY年M月D日

    非空但无法识别 → ValueError（消息含 \"invalid date\"）
    """
    # TODO
    raise NotImplementedError


def format_constraints(constraints: Sequence[str]) -> str:
    """Markdown 无序列表；跳过空项；每项 strip。有效项为空 → ValueError(\"constraints\")。"""
    # TODO
    raise NotImplementedError


def build_minutes_system_prompt(
    *,
    role: str = DEFAULT_ROLE,
    task: str = DEFAULT_TASK,
    constraints: Sequence[str] | None = None,
) -> str:
    """组装 system Prompt。

    章节顺序：角色 → 任务 → 约束 → 输出格式
    - role / task 空 → ValueError（消息含字段名）
    - constraints 为 None 时用 DEFAULT_CONSTRAINTS
    - 输出格式正文 = \"JSON Schema:\\n\" + schema_for_prompt(MeetingMinutes)
    """
    # TODO
    raise NotImplementedError


def wrap_minutes_text(text: str) -> str:
    """用边界标记包裹会议原文。

    格式（注意换行）：
        【会议原文】
        {text.strip()}
        【会议原文结束】

    text 全空白 → ValueError（含 \"text\"）
    """
    # TODO
    raise NotImplementedError


def build_minutes_messages(text: str) -> list[dict[str, str]]:
    """返回 [system, user] 两条消息。"""
    # TODO
    raise NotImplementedError


def parse_minutes(raw: str) -> MeetingMinutes:
    """从模型原始回复解析 MeetingMinutes。

    - extract_json_object → json.loads → 规范化日期字段 → MeetingMinutes.model_validate
    - 对 data[\"meeting_date\"] 以及每条 action_items[*][\"due_date\"] 调用 normalize_date
      （字段缺失则跳过；存在则写入规范化结果）
    - ValidationError → 包装为 ValueError(\"validation failed: ...\")
    - JSON 解码失败 → ValueError（含 \"invalid json\"）
    """
    # TODO
    raise NotImplementedError


def extract_minutes(text: str, complete_fn: CompleteFn) -> MeetingMinutes:
    """调用 complete_fn(messages) 并 parse_minutes。

    text 全空白 → ValueError（含 \"text\"），不调用模型。
    """
    # TODO
    raise NotImplementedError


def minutes_to_markdown(minutes: MeetingMinutes) -> str:
    """渲染便于人读的 Markdown。

    结构（注意空行）：
    # {title}

    - 日期：{meeting_date 或 \"未注明\"}
    - 参会：{顿号连接 attendees；空则 \"未注明\"}

    ## 决议
    若无决议：一行 \"（无）\"
    否则有序列表：1. ... / 2. ...

    ## Action Items
    若无行动项：一行 \"（无）\"
    否则无序列表，每项格式：
    - [{priority}] {owner}：{task}（截止：{due_date 或 \"未定\"}）

    末尾保留一个换行。
    """
    # TODO
    raise NotImplementedError


def action_items_to_csv(items: Sequence[ActionItem]) -> str:
    """导出行动项 CSV（含表头）。

    - 列顺序固定为 CSV_FIELDS
    - 空值写空字符串
    - 使用 csv 模块，lineterminator=\"\\n\"
    - 无数据时仍要有表头行
    """
    # TODO
    raise NotImplementedError


def minutes_to_json(minutes: MeetingMinutes, *, indent: int | None = 2) -> str:
    """导出单个纪要 JSON 对象字符串（ensure_ascii=False）。"""
    # TODO
    raise NotImplementedError


def minutes_summary(minutes: MeetingMinutes) -> dict[str, int | list[str]]:
    """返回摘要统计。

    {
      \"decisions\": int,
      \"action_items\": int,
      \"attendees\": int,
      \"owners\": 去重后的负责人列表（按首次出现顺序）
    }
    """
    # TODO
    raise NotImplementedError
