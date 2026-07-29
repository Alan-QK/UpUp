"""Day 7：RetryingJsonClient 测试（全部离线 Mock）。"""

from __future__ import annotations

import httpx
import pytest

from retry_client import (
    HttpResponseError,
    HttpStatusError,
    RetryingJsonClient,
    is_retryable_exception,
    is_retryable_status,
)


def test_is_retryable_status() -> None:
    assert is_retryable_status(429) is True
    assert is_retryable_status(500) is True
    assert is_retryable_status(503) is True
    assert is_retryable_status(400) is False
    assert is_retryable_status(404) is False
    assert is_retryable_status(200) is False


def test_is_retryable_exception() -> None:
    assert is_retryable_exception(httpx.TimeoutException("t")) is True
    assert is_retryable_exception(httpx.ConnectError("c")) is True
    assert is_retryable_exception(HttpStatusError(503, "x")) is True
    assert is_retryable_exception(HttpStatusError(429, "x")) is True
    assert is_retryable_exception(HttpStatusError(404, "x")) is False
    assert is_retryable_exception(HttpResponseError("bad")) is False
    assert is_retryable_exception(ValueError("nope")) is False


def test_retries_then_succeeds() -> None:
    calls = {"n": 0}
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503, json={"error": "busy"})
        return httpx.Response(200, json={"ok": True})

    client = RetryingJsonClient(
        "https://api.test",
        max_retries=2,
        backoff_seconds=0.05,
        transport=httpx.MockTransport(handler),
        sleep=sleeps.append,
    )
    with client:
        data = client.get_json("/x")
    assert data == {"ok": True}
    assert calls["n"] == 3
    assert sleeps == [0.05, 0.10]


def test_gives_up_after_max_retries() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(502, json={"error": "bad gateway"})

    with RetryingJsonClient(
        "https://api.test",
        max_retries=2,
        backoff_seconds=0.01,
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    ) as client:
        with pytest.raises(HttpStatusError) as ei:
            client.get_json("/x")
    assert ei.value.status_code == 502
    assert calls["n"] == 3


def test_does_not_retry_client_errors() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(404, json={"error": "missing"})

    with RetryingJsonClient(
        "https://api.test",
        max_retries=5,
        backoff_seconds=0.01,
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    ) as client:
        with pytest.raises(HttpStatusError) as ei:
            client.get_json("/missing")
    assert ei.value.status_code == 404
    assert calls["n"] == 1


def test_retries_timeout_then_ok() -> None:
    calls = {"n": 0}
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ReadTimeout("slow")
        return httpx.Response(200, json={"recovered": True})

    with RetryingJsonClient(
        "https://api.test",
        max_retries=1,
        backoff_seconds=0.02,
        transport=httpx.MockTransport(handler),
        sleep=sleeps.append,
    ) as client:
        data = client.get_json("/slow")
    assert data == {"recovered": True}
    assert calls["n"] == 2
    assert sleeps == [0.02]


def test_invalid_json_not_retried() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, text="not-json", headers={"content-type": "text/plain"})

    with RetryingJsonClient(
        "https://api.test",
        max_retries=3,
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    ) as client:
        with pytest.raises(HttpResponseError):
            client.get_json("/plain")
    assert calls["n"] == 1


def test_post_json_retries() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        assert request.method == "POST"
        if calls["n"] == 1:
            return httpx.Response(429, json={"error": "rate"})
        return httpx.Response(200, json={"created": True})

    with RetryingJsonClient(
        "https://api.test",
        max_retries=1,
        backoff_seconds=0.01,
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    ) as client:
        data = client.post_json("/items", json={"name": "a"})
    assert data == {"created": True}
    assert calls["n"] == 2
