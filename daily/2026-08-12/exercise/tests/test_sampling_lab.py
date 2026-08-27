"""Day 17：采样参数校验、多样性指标与 temperature 扫描（全部离线 Mock）。"""

from __future__ import annotations

import json

import httpx
import pytest

from chat_client import ChatClient, ChatMessage
from sampling_lab import (
    SamplingRun,
    format_comparison_report,
    jaccard_distance,
    run_temperature_sweep,
    tokenize,
    unique_token_ratio,
    validate_temperature,
    validate_top_p,
)


def _ok_payload(content: str, *, model: str = "gpt-4o-mini") -> dict:
    return {
        "id": "chatcmpl-test",
        "model": model,
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": content},
            }
        ],
        "usage": {
            "prompt_tokens": 8,
            "completion_tokens": 4,
            "total_tokens": 12,
        },
    }


def _make_client(handler) -> ChatClient:
    return ChatClient(
        "https://api.test/v1",
        "sk-test",
        model="gpt-4o-mini",
        transport=httpx.MockTransport(handler),
    )


def test_validate_temperature_bounds() -> None:
    assert validate_temperature(0.0) == 0.0
    assert validate_temperature(1.0) == 1.0
    assert validate_temperature(2.0) == 2.0
    with pytest.raises(ValueError, match=r"temperature must be in \[0, 2\]"):
        validate_temperature(-0.1)
    with pytest.raises(ValueError, match=r"temperature must be in \[0, 2\]"):
        validate_temperature(2.01)


def test_validate_top_p_bounds() -> None:
    assert validate_top_p(0.1) == 0.1
    assert validate_top_p(1.0) == 1.0
    with pytest.raises(ValueError, match=r"top_p must be in \(0, 1\]"):
        validate_top_p(0.0)
    with pytest.raises(ValueError, match=r"top_p must be in \(0, 1\]"):
        validate_top_p(1.1)


def test_tokenize_and_unique_ratio() -> None:
    assert tokenize("") == []
    assert tokenize("Hello, HELLO world!") == ["hello", "hello", "world"]
    assert tokenize("前端 Agent 前端") == ["前端", "agent", "前端"]
    assert unique_token_ratio("") == 0.0
    assert unique_token_ratio("a a a") == pytest.approx(1 / 3)
    assert unique_token_ratio("a b c") == pytest.approx(1.0)


def test_jaccard_distance() -> None:
    assert jaccard_distance("", "") == 0.0
    assert jaccard_distance("cat dog", "cat dog") == pytest.approx(0.0)
    # {a,b} vs {b,c} → intersection 1, union 3 → distance 2/3
    assert jaccard_distance("a b", "b c") == pytest.approx(2 / 3)
    assert jaccard_distance("alpha", "beta") == pytest.approx(1.0)


def test_run_temperature_sweep_empty() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not call API for empty sweep")

    client = _make_client(handler)
    assert (
        run_temperature_sweep(
            client,
            [ChatMessage("user", "hi")],
            [],
        )
        == []
    )


def test_run_temperature_sweep_validates_before_call() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json=_ok_payload("x"))

    client = _make_client(handler)
    with pytest.raises(ValueError, match="temperature"):
        run_temperature_sweep(
            client,
            [ChatMessage("user", "hi")],
            [0.5, 3.0],
        )
    assert calls["n"] == 0


def test_run_temperature_sweep_sends_params_and_order() -> None:
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        seen.append(body)
        temp = body.get("temperature")
        content = f"reply@{temp}"
        return httpx.Response(200, json=_ok_payload(content))

    client = _make_client(handler)
    messages = [
        ChatMessage("system", "简洁回答"),
        ChatMessage("user", "用一句话介绍温度参数"),
    ]
    runs = run_temperature_sweep(
        client,
        messages,
        [0.0, 0.7, 1.5],
        top_p=0.9,
    )

    assert [r.temperature for r in runs] == [0.0, 0.7, 1.5]
    assert all(r.top_p == 0.9 for r in runs)
    assert [r.content for r in runs] == ["reply@0.0", "reply@0.7", "reply@1.5"]
    assert [b["temperature"] for b in seen] == [0.0, 0.7, 1.5]
    assert all(b["top_p"] == 0.9 for b in seen)
    assert all(b["stream"] is False for b in seen)


def test_format_comparison_report_empty() -> None:
    text = format_comparison_report([])
    assert text.startswith("# Temperature Sweep Report\n")
    assert "（无采样结果）" in text
    assert text.endswith("\n")


def test_format_comparison_report_with_pairwise() -> None:
    runs = [
        SamplingRun(0.0, None, "答案是四十二。答案是四十二。"),
        SamplingRun(1.2, 0.95, "火焰蓝鲸说芒果派才是答案！"),
    ]
    text = format_comparison_report(runs)
    assert text.startswith("# Temperature Sweep Report\n")
    assert "## temperature=0.0" in text
    assert "top_p=default" in text
    assert "## temperature=1.2" in text
    assert "top_p=0.95" in text
    assert "chars=" in text
    assert "unique_token_ratio=" in text
    assert "preview=" in text
    assert "## Pairwise Jaccard Distance" in text
    assert "t0-t1:" in text
    assert text.endswith("\n")
