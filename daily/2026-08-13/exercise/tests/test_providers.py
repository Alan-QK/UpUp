"""Day 18：Provider 协议、Fake 与工厂。"""

from __future__ import annotations

import json

import httpx
import pytest

from openai_compat import OpenAICompatProvider
from providers import (
    ChatCompletionResult,
    ChatMessage,
    ChatProvider,
    FakeChatProvider,
    ProviderCall,
    ProviderError,
    create_chat_provider,
    last_user_content,
)


def test_last_user_content() -> None:
    messages = [
        ChatMessage("system", "sys"),
        ChatMessage("user", "u1"),
        ChatMessage("assistant", "a1"),
        ChatMessage("user", "u2"),
    ]
    assert last_user_content(messages) == "u2"
    assert last_user_content([ChatMessage("system", "only")]) == ""


def test_fake_lookup_and_default() -> None:
    fake = FakeChatProvider(
        model="m-fake",
        default_reply="fallback",
        replies={"hello": "world"},
    )
    assert fake.name == "fake"
    assert isinstance(fake, ChatProvider)

    hit = fake.complete(
        [
            ChatMessage("system", "s"),
            ChatMessage("user", "hello"),
        ],
        temperature=0.5,
        top_p=0.9,
    )
    assert hit == ChatCompletionResult(
        content="world",
        model="m-fake",
        finish_reason="stop",
        prompt_tokens=1 + 5,  # "s" + "hello"
        completion_tokens=5,  # "world"
        total_tokens=11,
    )

    miss = fake.complete([ChatMessage("user", "other")])
    assert miss.content == "fallback"
    assert miss.completion_tokens == len("fallback")

    assert len(fake.calls) == 2
    assert fake.calls[0] == ProviderCall(
        messages=(
            ChatMessage("system", "s"),
            ChatMessage("user", "hello"),
        ),
        temperature=0.5,
        top_p=0.9,
    )
    fake.close()  # 不应抛错


def test_fake_empty_messages() -> None:
    fake = FakeChatProvider()
    with pytest.raises(ProviderError, match="messages must not be empty"):
        fake.complete([])


def test_create_fake_provider() -> None:
    provider = create_chat_provider(
        " Fake ",
        model="x",
        default_reply="d",
        replies={"q": "a"},
    )
    assert provider.name == "fake"
    result = provider.complete([ChatMessage("user", "q")])
    assert result.content == "a"
    provider.close()


def test_create_openai_provider_with_mock_transport() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        assert body["stream"] is False
        assert body["model"] == "demo"
        return httpx.Response(
            200,
            json={
                "id": "1",
                "model": "demo",
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "hi"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 3,
                    "completion_tokens": 1,
                    "total_tokens": 4,
                },
            },
        )

    for kind in ("openai", "openai_compat", "OpenAI"):
        provider = create_chat_provider(
            kind,
            model="demo",
            api_key="sk-test",
            base_url="https://example.test/v1",
            transport=httpx.MockTransport(handler),
        )
        assert isinstance(provider, OpenAICompatProvider)
        assert provider.name == "openai_compat"
        result = provider.complete([ChatMessage("user", "ping")])
        assert result.content == "hi"
        assert result.total_tokens == 4
        provider.close()


def test_create_provider_errors() -> None:
    with pytest.raises(ProviderError, match="provider kind must not be empty"):
        create_chat_provider("  ", model="m")
    with pytest.raises(ProviderError, match="unknown provider kind: anthropic"):
        create_chat_provider("anthropic", model="m")


def test_openai_compat_rejects_empty_messages() -> None:
    provider = OpenAICompatProvider(
        "https://example.test/v1",
        "sk",
        model="m",
        transport=httpx.MockTransport(lambda r: httpx.Response(500)),
    )
    with pytest.raises(ProviderError, match="messages must not be empty"):
        provider.complete([])
    provider.close()
