"""Day 30：会议纪要结构化 · 决议 + action items。"""

from __future__ import annotations

import csv
import io
import json
from typing import Any

import pytest

from meeting_minutes import (
    CSV_FIELDS,
    DEFAULT_CONSTRAINTS,
    SECTION_CONSTRAINTS,
    SECTION_OUTPUT_FORMAT,
    SECTION_ROLE,
    SECTION_TASK,
    ActionItem,
    MeetingMinutes,
    action_items_to_csv,
    build_minutes_messages,
    build_minutes_system_prompt,
    extract_minutes,
    format_constraints,
    minutes_summary,
    minutes_to_json,
    minutes_to_markdown,
    normalize_date,
    parse_minutes,
    wrap_minutes_text,
)


def _ok_payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "title": "Sprint 评审",
        "meeting_date": "2026-09-02",
        "attendees": ["Alice", "Bob"],
        "decisions": ["采用方案 B"],
        "action_items": [
            {
                "owner": "Alice",
                "task": "更新发布计划",
                "due_date": "2026-09-05",
                "priority": "high",
            }
        ],
    }
    base.update(overrides)
    return base


def test_normalize_date() -> None:
    assert normalize_date(None) is None
    assert normalize_date("  ") is None
    assert normalize_date("2026-09-02") == "2026-09-02"
    assert normalize_date("2026/9/5") == "2026-09-05"
    assert normalize_date("2026/09/05") == "2026-09-05"
    assert normalize_date("2026年9月2日") == "2026-09-02"
    with pytest.raises(ValueError, match="invalid date"):
        normalize_date("明天")


def test_format_constraints_and_prompt() -> None:
    text = format_constraints(["  a  ", "", "b"])
    assert text == "- a\n- b"
    with pytest.raises(ValueError, match="constraints"):
        format_constraints(["  ", ""])

    prompt = build_minutes_system_prompt()
    assert f"【{SECTION_ROLE}】" in prompt
    assert f"【{SECTION_TASK}】" in prompt
    assert f"【{SECTION_CONSTRAINTS}】" in prompt
    assert f"【{SECTION_OUTPUT_FORMAT}】" in prompt
    assert "JSON Schema:" in prompt
    assert "action_items" in prompt or "MeetingMinutes" in prompt
    for c in DEFAULT_CONSTRAINTS:
        assert c in prompt

    with pytest.raises(ValueError, match="role"):
        build_minutes_system_prompt(role="  ")
    with pytest.raises(ValueError, match="task"):
        build_minutes_system_prompt(task="")


def test_wrap_and_messages() -> None:
    wrapped = wrap_minutes_text("  开会了\n决议：上线  ")
    assert wrapped.startswith("【会议原文】\n")
    assert wrapped.endswith("\n【会议原文结束】")
    assert "开会了\n决议：上线" in wrapped
    with pytest.raises(ValueError, match="text"):
        wrap_minutes_text("   ")

    messages = build_minutes_messages("今日例会")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "【会议原文】" in messages[1]["content"]
    assert "今日例会" in messages[1]["content"]


def test_parse_minutes_plain_and_fence() -> None:
    plain = "结果：" + json.dumps(_ok_payload(), ensure_ascii=False)
    m = parse_minutes(plain)
    assert m.title == "Sprint 评审"
    assert m.meeting_date == "2026-09-02"
    assert m.action_items[0].priority == "high"

    fenced = (
        "好的\n```json\n"
        + json.dumps(
            _ok_payload(
                meeting_date="2026年9月2日",
                action_items=[
                    {
                        "owner": "Bob",
                        "task": "同步设计",
                        "due_date": "2026/9/8",
                        "priority": "medium",
                    }
                ],
            ),
            ensure_ascii=False,
        )
        + "\n```\n"
    )
    m2 = parse_minutes(fenced)
    assert m2.meeting_date == "2026-09-02"
    assert m2.action_items[0].due_date == "2026-09-08"


def test_parse_minutes_validation_and_json_errors() -> None:
    empty_all = json.dumps(
        {
            "title": "空会",
            "decisions": [],
            "action_items": [],
        },
        ensure_ascii=False,
    )
    with pytest.raises(ValueError, match="validation failed"):
        parse_minutes(empty_all)

    bad_priority = json.dumps(
        _ok_payload(
            action_items=[
                {"owner": "A", "task": "x", "due_date": None, "priority": "urgent"}
            ]
        ),
        ensure_ascii=False,
    )
    with pytest.raises(ValueError, match="validation failed"):
        parse_minutes(bad_priority)

    with pytest.raises(ValueError, match="invalid json|no JSON"):
        parse_minutes("抱歉，我没法整理")


def test_extract_minutes_and_exports() -> None:
    payload = _ok_payload(
        meeting_date="2026/09/02",
        decisions=["延期一周", "采用方案 B"],
        action_items=[
            {
                "owner": "Alice",
                "task": "更新计划",
                "due_date": "2026年9月5日",
                "priority": "high",
            },
            {
                "owner": "Alice",
                "task": "通知客户",
                "due_date": None,
                "priority": "low",
            },
            {
                "owner": "Bob",
                "task": "准备演示",
                "due_date": "2026-09-10",
                "priority": "medium",
            },
        ],
    )

    def complete_fn(messages: list[dict[str, str]]) -> str:
        assert "【会议原文】" in messages[1]["content"]
        return "```json\n" + json.dumps(payload, ensure_ascii=False) + "\n```"

    minutes = extract_minutes("随便一段会议原文", complete_fn)
    assert minutes.meeting_date == "2026-09-02"
    assert minutes.action_items[0].due_date == "2026-09-05"

    with pytest.raises(ValueError, match="text"):
        extract_minutes("  ", complete_fn)

    summary = minutes_summary(minutes)
    assert summary["decisions"] == 2
    assert summary["action_items"] == 3
    assert summary["attendees"] == 2
    assert summary["owners"] == ["Alice", "Bob"]

    md = minutes_to_markdown(minutes)
    assert md.startswith("# Sprint 评审\n")
    assert "- 日期：2026-09-02" in md
    assert "- 参会：Alice、Bob" in md
    assert "## 决议" in md
    assert "1. 延期一周" in md
    assert "2. 采用方案 B" in md
    assert "## Action Items" in md
    assert "- [high] Alice：更新计划（截止：2026-09-05）" in md
    assert "- [low] Alice：通知客户（截止：未定）" in md
    assert md.endswith("\n")

    csv_text = action_items_to_csv(minutes.action_items)
    reader = csv.DictReader(io.StringIO(csv_text))
    assert reader.fieldnames == list(CSV_FIELDS)
    rows = list(reader)
    assert len(rows) == 3
    assert rows[0]["owner"] == "Alice"
    assert rows[0]["due_date"] == "2026-09-05"
    assert rows[1]["due_date"] == ""

    empty_csv = action_items_to_csv([])
    assert empty_csv.startswith("owner,task,due_date,priority\n")

    dumped = json.loads(minutes_to_json(minutes))
    assert dumped["title"] == "Sprint 评审"
    assert len(dumped["action_items"]) == 3


def test_minutes_to_markdown_empty_sections() -> None:
    only_decision = MeetingMinutes(
        title="短会",
        meeting_date=None,
        attendees=[],
        decisions=["维持现状"],
        action_items=[],
    )
    md = minutes_to_markdown(only_decision)
    assert "- 日期：未注明" in md
    assert "- 参会：未注明" in md
    assert "1. 维持现状" in md
    assert "## Action Items\n（无）" in md

    only_action = MeetingMinutes(
        title="短会2",
        decisions=[],
        action_items=[ActionItem(owner="Carol", task="写纪要", due_date=None)],
    )
    md2 = minutes_to_markdown(only_action)
    assert "## 决议\n（无）" in md2
    assert "- [medium] Carol：写纪要（截止：未定）" in md2
