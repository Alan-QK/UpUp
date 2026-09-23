"""Day 14：UsageLedger / token 估算 / 费用计算测试。"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from usage_meter import (
    DEFAULT_PRICING,
    ModelPricing,
    UsageLedger,
    calculate_cost_usd,
    estimate_tokens,
    join_message_contents,
)


def test_estimate_tokens_empty_and_cjk_ascii() -> None:
    assert estimate_tokens("") == 0
    assert estimate_tokens("你好") == 2
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcdefgh") == 2
    assert estimate_tokens("你好abcd") == 3


def test_estimate_tokens_mixed_punctuation() -> None:
    # 「Hi」= 2 other → (2+3)//4 = 1；「，」= 1 other → 再计；简化：整段非 CJK
    assert estimate_tokens("Hi") == 1
    assert estimate_tokens("测试test") == 2 + 1  # 测/试 + test(4→1)


def test_calculate_cost_usd_rounds_to_8() -> None:
    pricing = DEFAULT_PRICING["gpt-4o-mini"]
    # 12 * 0.15 / 1e6 + 8 * 0.60 / 1e6 = 0.0000066
    assert calculate_cost_usd(12, 8, pricing) == 0.0000066
    assert calculate_cost_usd(0, 0, pricing) == 0.0


def test_calculate_cost_demo_pricing() -> None:
    pricing = DEFAULT_PRICING["demo-model"]
    # 1000 * 1 / 1e6 + 500 * 2 / 1e6 = 0.001 + 0.001 = 0.002
    assert calculate_cost_usd(1000, 500, pricing) == 0.002


def test_join_message_contents_supports_str_dict_object() -> None:
    @dataclass
    class Msg:
        content: str

    text = join_message_contents(
        [
            "system-line",
            {"role": "user", "content": "user-line"},
            Msg(content="assistant-line"),
        ]
    )
    assert text == "system-line\nuser-line\nassistant-line"


def test_record_rejects_negative_tokens() -> None:
    ledger = UsageLedger()
    pricing = DEFAULT_PRICING["demo-model"]
    with pytest.raises(ValueError, match="tokens must be non-negative"):
        ledger.record(
            model="demo-model",
            prompt_tokens=-1,
            completion_tokens=0,
            pricing=pricing,
            source="api",
        )


def test_record_and_records_are_copy() -> None:
    ledger = UsageLedger()
    pricing = ModelPricing("x", 1.0, 2.0)
    rec = ledger.record(
        model="x",
        prompt_tokens=10,
        completion_tokens=5,
        pricing=pricing,
        source="api",
    )
    assert rec.total_tokens == 15
    assert rec.cost_usd == calculate_cost_usd(10, 5, pricing)
    assert rec.source == "api"

    snapshot = ledger.records
    snapshot.clear()
    assert len(ledger.records) == 1


def test_record_from_texts_uses_estimate() -> None:
    ledger = UsageLedger()
    pricing = DEFAULT_PRICING["gpt-4o-mini"]
    rec = ledger.record_from_texts(
        model="gpt-4o-mini",
        prompt_text="你好abcd",
        completion_text="好的",
        pricing=pricing,
    )
    assert rec.source == "estimate"
    assert rec.prompt_tokens == 3
    assert rec.completion_tokens == 2
    assert rec.total_tokens == 5


def test_record_from_api_usage_prefers_api() -> None:
    ledger = UsageLedger()
    pricing = DEFAULT_PRICING["gpt-4o-mini"]
    rec = ledger.record_from_api_usage(
        model="gpt-4o-mini",
        prompt_tokens=12,
        completion_tokens=8,
        pricing=pricing,
        prompt_text="会被忽略的长文本" * 20,
        completion_text="也会被忽略",
    )
    assert rec.source == "api"
    assert rec.prompt_tokens == 12
    assert rec.completion_tokens == 8
    assert rec.total_tokens == 20


def test_record_from_api_usage_fallback_estimate() -> None:
    ledger = UsageLedger()
    pricing = DEFAULT_PRICING["demo-model"]
    rec = ledger.record_from_api_usage(
        model="demo-model",
        prompt_tokens=None,
        completion_tokens=4,
        pricing=pricing,
        prompt_text="abcd",
        completion_text="ignored-because-api-side-present",
    )
    assert rec.source == "estimate"
    assert rec.prompt_tokens == 1
    assert rec.completion_tokens == 4


def test_format_log_line_and_summary() -> None:
    ledger = UsageLedger()
    pricing = DEFAULT_PRICING["gpt-4o-mini"]
    r1 = ledger.record(
        model="gpt-4o-mini",
        prompt_tokens=12,
        completion_tokens=8,
        pricing=pricing,
        source="api",
    )
    ledger.record_from_texts(
        model="gpt-4o-mini",
        prompt_text="你好",
        completion_text="好",
        pricing=pricing,
    )

    line = ledger.format_log_line(r1)
    assert (
        line
        == "usage model=gpt-4o-mini prompt=12 completion=8 total=20 cost_usd=0.00000660 source=api"
    )

    summary = ledger.format_summary()
    lines = summary.splitlines()
    assert lines[0].startswith("usage_summary calls=2 ")
    assert "total_tokens=23" in lines[0]  # 20 + (2+1)
    assert lines[1] == line
    assert "source=estimate" in lines[2]

    assert ledger.total_tokens() == 23
    assert ledger.total_cost_usd() == round(r1.cost_usd + ledger.records[1].cost_usd, 8)


def test_empty_summary() -> None:
    ledger = UsageLedger()
    assert (
        ledger.format_summary()
        == "usage_summary calls=0 total_tokens=0 total_cost_usd=0.00000000"
    )
