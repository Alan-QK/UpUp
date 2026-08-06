"""Day 11：ChatClient 测试（全部离线 Mock）。"""

from __future__ import annotations

import json

import httpx
import pytest

from chat_client import (
    ChatClient,
    ChatCompletionResult,
    ChatHttpError,
    ChatMessage,
    ChatResponseError,
)


def _ok_payload(
    *,
    content: str = "你好，我是助手。",
    model: str = "gpt-4o-mini",
    finish_reason: str = "stop",
    include_usage: bool = True,
) -> dict:
    data: dict = {
        "id": "chatcmpl-test",
        "model": model,
        "choices": [
            {
                "index": 0,
                "finish_reason": finish_reason,
                "message": {"role": "assistant", "content": content},
            }
        ],
    }
    if include_usage:
        data["usage"] = {
            "prompt_tokens": 12,
            "completion_tokens": 8,
            "total_tokens": 20,
        }
    return data


def _make_handler(
    *,
    expected_model: str = "gpt-4o-mini",
    expected_key: str = "sk-test",
    response_factory=None,
):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path.endswith("/chat/completions")
        auth = request.headers.get("Authorization", "")
        assert auth == f"Bearer {expected_key}"

        body = json.loads(request.content.decode("utf-8") or "{}")
        assert body.get("stream") is False
        assert body.get("model") == expected_model
        assert isinstance(body.get("messages"), list)

        if response_factory is not None:
            return response_factory(request, body)

        return httpx.Response(200, json=_ok_payload(model=expected_model))

    return handler


@pytest.fixture
def client() -> ChatClient:
    transport = httpx.MockTransport(_make_handler())
    with ChatClient(
        "https://api.test/v1",
        "sk-test",
        model="gpt-4o-mini",
        transport=transport,
    ) as c:
        yield c


def test_complete_returns_content_and_usage(client: ChatClient) -> None:
    result = client.complete([ChatMessage(role="user", content="你好")])
    assert isinstance(result, ChatCompletionResult)
    assert result.content == "你好，我是助手。"
    assert result.model == "gpt-4o-mini"
    assert result.finish_reason == "stop"
    assert result.prompt_tokens == 12
    assert result.completion_tokens == 8
    assert result.total_tokens == 20


def test_complete_sends_messages_and_optional_temperature() -> None:
    captured: dict = {}

    def factory(request: httpx.Request, body: dict) -> httpx.Response:
        captured["body"] = body
        return httpx.Response(200, json=_ok_payload(content="ok"))

    transport = httpx.MockTransport(
        _make_handler(response_factory=factory)
    )
    with ChatClient(
        "https://api.test/v1",
        "sk-test",
        model="gpt-4o-mini",
        transport=transport,
    ) as c:
        c.complete(
            [
                ChatMessage(role="system", content="简洁回答"),
                ChatMessage(role="user", content="1+1=?"),
            ],
            temperature=0.2,
        )

    assert captured["body"]["messages"] == [
        {"role": "system", "content": "简洁回答"},
        {"role": "user", "content": "1+1=?"},
    ]
    assert captured["body"]["temperature"] == 0.2
    assert captured["body"]["stream"] is False


def test_http_error() -> None:
    def factory(request: httpx.Request, body: dict) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "invalid key"}})

    transport = httpx.MockTransport(_make_handler(response_factory=factory))
    with ChatClient(
        "https://api.test/v1",
        "sk-test",
        model="gpt-4o-mini",
        transport=transport,
    ) as c:
        with pytest.raises(ChatHttpError) as ei:
            c.complete([ChatMessage(role="user", content="hi")])
    assert ei.value.status_code == 401
    assert "invalid key" in ei.value.body


def test_invalid_json_raises() -> None:
    def factory(request: httpx.Request, body: dict) -> httpx.Response:
        return httpx.Response(
            200, text="not-json", headers={"content-type": "text/plain"}
        )

    transport = httpx.MockTransport(_make_handler(response_factory=factory))
    with ChatClient(
        "https://api.test/v1",
        "sk-test",
        model="gpt-4o-mini",
        transport=transport,
    ) as c:
        with pytest.raises(ChatResponseError):
            c.complete([ChatMessage(role="user", content="hi")])


def test_missing_choices_raises() -> None:
    def factory(request: httpx.Request, body: dict) -> httpx.Response:
        return httpx.Response(200, json={"id": "x", "model": "gpt-4o-mini"})

    transport = httpx.MockTransport(_make_handler(response_factory=factory))
    with ChatClient(
        "https://api.test/v1",
        "sk-test",
        model="gpt-4o-mini",
        transport=transport,
    ) as c:
        with pytest.raises(ChatResponseError):
            c.complete([ChatMessage(role="user", content="hi")])


def test_model_fallback_when_response_omits_model() -> None:
    def factory(request: httpx.Request, body: dict) -> httpx.Response:
        payload = _ok_payload(content="fallback", include_usage=False)
        del payload["model"]
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(
        _make_handler(expected_model="local-mini", response_factory=factory)
    )
    with ChatClient(
        "https://api.test/v1",
        "sk-test",
        model="local-mini",
        transport=transport,
    ) as c:
        result = c.complete([ChatMessage(role="user", content="hi")])
    assert result.model == "local-mini"
    assert result.prompt_tokens is None
    assert result.total_tokens is None


def test_context_manager_closes() -> None:
    transport = httpx.MockTransport(_make_handler())
    client = ChatClient(
        "https://api.test/v1",
        "sk-test",
        model="gpt-4o-mini",
        transport=transport,
    )
    with client:
        assert client.complete(
            [ChatMessage(role="user", content="x")]
        ).content
    with pytest.raises(RuntimeError):
        client.complete([ChatMessage(role="user", content="y")])
