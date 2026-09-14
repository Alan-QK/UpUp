"""Day 13：StreamingChatClient 测试（全部离线 Mock）。"""

from __future__ import annotations

import io
import json

import httpx
import pytest

from streaming_client import (
    ChatHttpError,
    ChatMessage,
    ChatResponseError,
    StreamingChatClient,
    extract_delta_text,
    parse_sse_data_line,
    print_stream,
)


def _sse_body(chunks: list[dict], *, trailing_done: bool = True) -> bytes:
    parts: list[str] = []
    for obj in chunks:
        parts.append(f"data: {json.dumps(obj, ensure_ascii=False)}\n\n")
    if trailing_done:
        parts.append("data: [DONE]\n\n")
    return "".join(parts).encode("utf-8")


def _delta(content: str | None = None, *, role: str | None = None) -> dict:
    delta: dict = {}
    if role is not None:
        delta["role"] = role
    if content is not None:
        delta["content"] = content
    return {"id": "chatcmpl-test", "choices": [{"index": 0, "delta": delta}]}


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
        assert body.get("stream") is True
        assert body.get("model") == expected_model
        assert isinstance(body.get("messages"), list)

        if response_factory is not None:
            return response_factory(request, body)

        content = _sse_body(
            [
                _delta(role="assistant"),
                _delta("你"),
                _delta("好"),
                {
                    "id": "chatcmpl-test",
                    "model": expected_model,
                    "choices": [
                        {"index": 0, "delta": {}, "finish_reason": "stop"}
                    ],
                },
            ]
        )
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=content,
        )

    return handler


def test_parse_sse_data_line_basic() -> None:
    assert parse_sse_data_line("data: {\"a\":1}") == '{"a":1}'
    assert parse_sse_data_line("data:{\"a\":1}") == '{"a":1}'
    assert parse_sse_data_line("data: [DONE]") == "[DONE]"
    assert parse_sse_data_line("data:[DONE]") == "[DONE]"
    assert parse_sse_data_line("") is None
    assert parse_sse_data_line(": comment") is None
    assert parse_sse_data_line("event: message") is None
    assert parse_sse_data_line("data: hello\r") == "hello"


def test_extract_delta_text() -> None:
    assert extract_delta_text(_delta("Hi")) == "Hi"
    assert extract_delta_text(_delta("")) == ""
    assert extract_delta_text(_delta(role="assistant")) is None
    assert extract_delta_text({"choices": []}) is None
    assert extract_delta_text({"choices": [{"delta": {"content": 1}}]}) is None
    assert extract_delta_text({}) is None


def test_print_stream_flushes_and_joins() -> None:
    buf = io.StringIO()
    text = print_stream(["你", "好", "！"], file=buf)
    assert text == "你好！"
    assert buf.getvalue() == "你好！\n"


def test_iter_content_yields_deltas() -> None:
    transport = httpx.MockTransport(_make_handler())
    with StreamingChatClient(
        "https://api.test/v1",
        "sk-test",
        model="gpt-4o-mini",
        transport=transport,
    ) as client:
        parts = list(
            client.iter_content([ChatMessage(role="user", content="hi")])
        )
    assert parts == ["你", "好"]


def test_iter_content_sends_stream_true_and_temperature() -> None:
    captured: dict = {}

    def factory(request: httpx.Request, body: dict) -> httpx.Response:
        captured["body"] = body
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=_sse_body([_delta("ok")]),
        )

    transport = httpx.MockTransport(
        _make_handler(response_factory=factory)
    )
    with StreamingChatClient(
        "https://api.test/v1",
        "sk-test",
        model="gpt-4o-mini",
        transport=transport,
    ) as client:
        text = "".join(
            client.iter_content(
                [
                    ChatMessage(role="system", content="简洁"),
                    ChatMessage(role="user", content="嗨"),
                ],
                temperature=0.1,
            )
        )

    assert text == "ok"
    assert captured["body"]["stream"] is True
    assert captured["body"]["temperature"] == 0.1
    assert captured["body"]["messages"] == [
        {"role": "system", "content": "简洁"},
        {"role": "user", "content": "嗨"},
    ]


def test_http_error() -> None:
    def factory(request: httpx.Request, body: dict) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": "rate limit"}})

    transport = httpx.MockTransport(_make_handler(response_factory=factory))
    with StreamingChatClient(
        "https://api.test/v1",
        "sk-test",
        model="gpt-4o-mini",
        transport=transport,
    ) as client:
        with pytest.raises(ChatHttpError) as ei:
            list(client.iter_content([ChatMessage(role="user", content="x")]))
    assert ei.value.status_code == 429
    assert "rate limit" in ei.value.body


def test_invalid_sse_json_raises() -> None:
    def factory(request: httpx.Request, body: dict) -> httpx.Response:
        raw = b"data: not-json\n\ndata: [DONE]\n\n"
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=raw,
        )

    transport = httpx.MockTransport(_make_handler(response_factory=factory))
    with StreamingChatClient(
        "https://api.test/v1",
        "sk-test",
        model="gpt-4o-mini",
        transport=transport,
    ) as client:
        with pytest.raises(ChatResponseError):
            list(client.iter_content([ChatMessage(role="user", content="x")]))


def test_stops_at_done_even_if_more_lines() -> None:
    def factory(request: httpx.Request, body: dict) -> httpx.Response:
        raw = (
            b"data: "
            + json.dumps(_delta("A"), ensure_ascii=False).encode()
            + b"\n\n"
            + b"data: [DONE]\n\n"
            + b"data: "
            + json.dumps(_delta("B"), ensure_ascii=False).encode()
            + b"\n\n"
        )
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=raw,
        )

    transport = httpx.MockTransport(_make_handler(response_factory=factory))
    with StreamingChatClient(
        "https://api.test/v1",
        "sk-test",
        model="gpt-4o-mini",
        transport=transport,
    ) as client:
        parts = list(
            client.iter_content([ChatMessage(role="user", content="x")])
        )
    assert parts == ["A"]
