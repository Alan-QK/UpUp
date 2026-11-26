"""Day 26：JSON 结构化输出 · pydantic 校验。"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from structured import (
    DEFAULT_CONSTRAINTS,
    DEFAULT_ROLE,
    DEFAULT_TASK,
    Priority,
    SECTION_CONSTRAINTS,
    SECTION_OUTPUT_FORMAT,
    SECTION_ROLE,
    SECTION_TASK,
    TaskBatch,
    TaskItem,
    build_structured_messages,
    build_structured_system_prompt,
    extract_json_object,
    format_constraints,
    join_sections,
    normalize_text,
    parse_and_render,
    parse_task_batch,
    schema_for_prompt,
    tasks_to_markdown,
    validation_error_summary,
)


SAMPLE = {
    "tasks": [
        {
            "id": "T-1",
            "title": "修登录",
            "priority": "high",
            "tags": ["auth"],
            "estimate_hours": 1.5,
        }
    ]
}


def test_normalize_text() -> None:
    assert normalize_text("  你好\n\n世界  ") == "你好 世界"
    assert normalize_text("a\tb  c") == "a b c"
    assert normalize_text("   ") == ""


def test_priority_enum_and_task_item() -> None:
    item = TaskItem.model_validate(
        {
            "id": "T-1",
            "title": "demo",
            "priority": "medium",
            "tags": [],
            "estimate_hours": None,
        }
    )
    assert item.priority is Priority.medium
    with pytest.raises(ValidationError):
        TaskItem.model_validate(
            {"id": "T-1", "title": "x", "priority": "紧急", "tags": []}
        )
    with pytest.raises(ValidationError):
        TaskItem.model_validate(
            {
                "id": "T-1",
                "title": "x",
                "priority": "low",
                "tags": [],
                "estimate_hours": -1,
            }
        )


def test_task_batch_min_one() -> None:
    with pytest.raises(ValidationError):
        TaskBatch.model_validate({"tasks": []})
    batch = TaskBatch.model_validate(SAMPLE)
    assert len(batch.tasks) == 1
    assert batch.tasks[0].title == "修登录"


def test_extract_json_object_plain_and_fence() -> None:
    plain = '前缀 {"a": 1} 后缀'
    assert extract_json_object(plain) == '{"a": 1}'

    fenced = """好的：
```json
{"tasks": [{"id": "T-1", "title": "x", "priority": "low"}]}
```
"""
    obj = extract_json_object(fenced)
    assert json.loads(obj)["tasks"][0]["id"] == "T-1"

    nested = '说：{"outer": {"inner": "{"}, "ok": true}'
    assert json.loads(extract_json_object(nested))["ok"] is True

    with pytest.raises(ValueError, match="empty"):
        extract_json_object("   ")
    with pytest.raises(ValueError):
        extract_json_object("no brace here")


def test_schema_for_prompt() -> None:
    text = schema_for_prompt(TaskBatch)
    data = json.loads(text)
    assert "properties" in data
    assert "tasks" in data["properties"]


def test_format_constraints_and_join_sections() -> None:
    assert format_constraints(["  A  ", "", " B\nB "]) == "- A\n- B B"
    assert format_constraints([]) == ""
    text = join_sections(
        [
            ("角色", "助理"),
            ("空", "  "),
            ("任务", "抽取"),
        ]
    )
    assert text == "【角色】\n助理\n\n【任务】\n抽取"


def test_build_structured_system_prompt() -> None:
    prompt = build_structured_system_prompt()
    assert f"【{SECTION_ROLE}】" in prompt
    assert f"【{SECTION_TASK}】" in prompt
    assert f"【{SECTION_CONSTRAINTS}】" in prompt
    assert f"【{SECTION_OUTPUT_FORMAT}】" in prompt
    assert "JSON Schema:" in prompt
    assert DEFAULT_ROLE.split("，")[0] in prompt or DEFAULT_ROLE in prompt
    assert "low" in prompt  # schema / 约束中应出现
    for c in DEFAULT_CONSTRAINTS[:2]:
        assert normalize_text(c) in prompt

    with pytest.raises(ValueError, match="role"):
        build_structured_system_prompt(role="  ")
    with pytest.raises(ValueError, match="task"):
        build_structured_system_prompt(task="")
    with pytest.raises(ValueError, match="constraints"):
        build_structured_system_prompt(constraints=["", "  "])


def test_build_structured_messages() -> None:
    messages = build_structured_messages("  做个登录页  ")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "做个登录页"
    assert DEFAULT_TASK[:4] in messages[0]["content"]
    with pytest.raises(ValueError, match="user"):
        build_structured_messages("  \n")


def test_validation_error_summary() -> None:
    with pytest.raises(ValidationError) as ei:
        TaskBatch.model_validate(
            {
                "tasks": [
                    {
                        "id": "",
                        "title": "x",
                        "priority": "nope",
                        "tags": [],
                        "estimate_hours": -2,
                    }
                ]
            }
        )
    lines = validation_error_summary(ei.value)
    assert lines
    assert any("priority" in line for line in lines)
    # 路径用 / 连接
    assert any("/" in line or line.split(":")[0] for line in lines)


def test_parse_task_batch_ok() -> None:
    raw = "如下：\n```json\n" + json.dumps(SAMPLE, ensure_ascii=False) + "\n```\n"
    batch = parse_task_batch(raw)
    assert batch.tasks[0].priority is Priority.high
    assert batch.tasks[0].estimate_hours == 1.5


def test_parse_task_batch_validation_failed() -> None:
    bad = json.dumps(
        {
            "tasks": [
                {
                    "id": "T-1",
                    "title": "x",
                    "priority": "紧急",
                    "tags": [],
                    "estimate_hours": -1,
                }
            ]
        },
        ensure_ascii=False,
    )
    with pytest.raises(ValueError, match="validation failed"):
        parse_task_batch(bad)


def test_parse_task_batch_invalid_json_payload() -> None:
    # 抽得出对象外形但 JSON 非法（尾逗号）
    with pytest.raises(ValueError, match="json"):
        parse_task_batch('{"tasks": [{"id": "T-1",},]}')


def test_tasks_to_markdown_and_render() -> None:
    batch = TaskBatch.model_validate(
        {
            "tasks": [
                {
                    "id": "T-1",
                    "title": "文档",
                    "priority": "low",
                    "tags": ["docs", "wiki"],
                    "estimate_hours": 1.0,
                },
                {
                    "id": "T-2",
                    "title": "排查",
                    "priority": "medium",
                    "tags": [],
                    "estimate_hours": 2.5,
                },
                {
                    "id": "T-3",
                    "title": "无估时",
                    "priority": "high",
                    "tags": [],
                    "estimate_hours": None,
                },
            ]
        }
    )
    md = tasks_to_markdown(batch)
    assert "- [T-1] 文档 (low) · tags: docs, wiki · ~1h" in md
    assert "- [T-2] 排查 (medium) · ~2.5h" in md
    assert "- [T-3] 无估时 (high)" in md
    assert "tags:" not in md.splitlines()[2]

    batch2, md2 = parse_and_render(json.dumps(SAMPLE, ensure_ascii=False))
    assert len(batch2.tasks) == 1
    assert "修登录" in md2
