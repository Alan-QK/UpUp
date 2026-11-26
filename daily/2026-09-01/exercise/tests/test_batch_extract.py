"""Day 29：批量信息抽取 · 文本 → Contact → JSON/CSV。"""

from __future__ import annotations

import csv
import io
import json
from typing import Any

import pytest

from batch_extract import (
    CSV_FIELDS,
    DEFAULT_CONSTRAINTS,
    SECTION_CONSTRAINTS,
    SECTION_OUTPUT_FORMAT,
    SECTION_ROLE,
    SECTION_TASK,
    Contact,
    ExtractResult,
    batch_summary,
    build_extract_messages,
    build_extract_system_prompt,
    contacts_to_csv,
    contacts_to_json,
    extract_batch,
    extract_json_object,
    extract_one,
    format_constraints,
    normalize_phone,
    parse_contact,
    successful_contacts,
    wrap_source_text,
)


def _ok_payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "name": "张三",
        "email": "zhangsan@example.com",
        "phone": "138-0000-1111",
        "company": "示例科技",
        "title": "前端工程师",
        "tags": ["frontend"],
    }
    base.update(overrides)
    return base


def test_normalize_phone() -> None:
    assert normalize_phone(None) is None
    assert normalize_phone("  ") is None
    assert normalize_phone("010-1234 5678") == "01012345678"
    assert normalize_phone("+86 138-0000-1111") == "+8613800001111"
    assert normalize_phone("abc") is None


def test_format_constraints_and_prompt() -> None:
    text = format_constraints(["  a  ", "", "b"])
    assert text == "- a\n- b"
    with pytest.raises(ValueError, match="constraints"):
        format_constraints(["  ", ""])

    prompt = build_extract_system_prompt()
    assert f"【{SECTION_ROLE}】" in prompt
    assert f"【{SECTION_TASK}】" in prompt
    assert f"【{SECTION_CONSTRAINTS}】" in prompt
    assert f"【{SECTION_OUTPUT_FORMAT}】" in prompt
    assert "JSON Schema:" in prompt
    assert "Contact" in prompt or "name" in prompt
    for c in DEFAULT_CONSTRAINTS:
        assert c in prompt

    with pytest.raises(ValueError, match="role"):
        build_extract_system_prompt(role="  ")
    with pytest.raises(ValueError, match="task"):
        build_extract_system_prompt(task="")


def test_wrap_and_messages() -> None:
    wrapped = wrap_source_text("  你好\n世界  ")
    assert wrapped.startswith("【原文】\n")
    assert wrapped.endswith("\n【原文结束】")
    assert "你好\n世界" in wrapped
    with pytest.raises(ValueError, match="text"):
        wrap_source_text("   ")

    messages = build_extract_messages("名片：李四")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "【原文】" in messages[1]["content"]
    assert "名片：李四" in messages[1]["content"]


def test_parse_contact_plain_and_fence() -> None:
    plain = "结果：" + json.dumps(_ok_payload(), ensure_ascii=False)
    c = parse_contact(plain)
    assert c.name == "张三"
    assert c.phone == "13800001111"

    fenced = (
        "好的\n```json\n"
        + json.dumps(_ok_payload(phone="+86 010-8888"), ensure_ascii=False)
        + "\n```\n"
    )
    c2 = parse_contact(fenced)
    assert c2.phone == "+860108888"


def test_parse_contact_validation_and_json_errors() -> None:
    bad_email = json.dumps(_ok_payload(email="not-an-email"), ensure_ascii=False)
    with pytest.raises(ValueError, match="validation failed"):
        parse_contact(bad_email)

    with pytest.raises(ValueError, match="invalid json|no JSON"):
        parse_contact("不好意思，没法抽取")

    broken = '前缀 {"name": "只有名字未闭合'
    with pytest.raises(ValueError):
        parse_contact(broken)


def test_extract_one_and_batch_isolation() -> None:
    mapping = {
        "名片A": json.dumps(_ok_payload(name="Alice"), ensure_ascii=False),
        "名片B": "这不是 JSON",
        "名片C": json.dumps(
            _ok_payload(name="Carol", email="carol@ex.com", tags=[]),
            ensure_ascii=False,
        ),
    }

    def complete_fn(messages: list[dict[str, str]]) -> str:
        user = messages[1]["content"]
        for key, raw in mapping.items():
            if key in user:
                return raw
        return "{}"

    r_ok = extract_one("a1", "请看名片A", complete_fn)
    assert r_ok.ok and r_ok.contact is not None
    assert r_ok.contact.name == "Alice"

    r_bad = extract_one("b1", "请看名片B", complete_fn)
    assert not r_bad.ok
    assert r_bad.error

    r_empty_id = extract_one("  ", "任意", complete_fn)
    assert not r_empty_id.ok
    assert "source_id" in (r_empty_id.error or "")

    items = [
        ("a1", "请看名片A"),
        ("b1", "请看名片B"),
        ("c1", "请看名片C"),
    ]
    results = extract_batch(items, complete_fn)
    assert len(results) == 3
    assert results[0].ok and results[2].ok
    assert not results[1].ok
    summary = batch_summary(results)
    assert summary == {"total": 3, "ok": 2, "failed": 1}
    contacts = successful_contacts(results)
    assert [c.name for c in contacts] == ["Alice", "Carol"]


def test_contacts_to_json_and_csv() -> None:
    contacts = [
        Contact(
            name="张三",
            email="a@b.com",
            phone="13800138000",
            company="Acme, Inc.",
            title="Eng",
            tags=["fe", "vue"],
        ),
        Contact(name="李四", email=None, phone=None, company=None, title=None, tags=[]),
    ]
    arr = json.loads(contacts_to_json(contacts))
    assert arr[0]["name"] == "张三"
    assert arr[0]["tags"] == ["fe", "vue"]
    assert arr[1]["email"] is None

    csv_text = contacts_to_csv(contacts)
    reader = csv.DictReader(io.StringIO(csv_text))
    assert reader.fieldnames == list(CSV_FIELDS)
    rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["company"] == "Acme, Inc."
    assert rows[0]["tags"] == "fe;vue"
    assert rows[1]["name"] == "李四"
    assert rows[1]["email"] == ""
    assert rows[1]["tags"] == ""

    empty_csv = contacts_to_csv([])
    assert empty_csv.startswith("name,email,phone,company,title,tags\n")
    assert len(empty_csv.strip().splitlines()) == 1


def test_extract_json_object_helper() -> None:
    assert extract_json_object('x {"a": 1} y') == '{"a": 1}'
    with pytest.raises(ValueError, match="empty"):
        extract_json_object("   ")


def test_contact_email_validator() -> None:
    with pytest.raises(Exception):
        Contact.model_validate({"name": "x", "email": "nope"})
    c = Contact.model_validate({"name": "x", "email": " ok@ex.com "})
    assert c.email == "ok@ex.com"
