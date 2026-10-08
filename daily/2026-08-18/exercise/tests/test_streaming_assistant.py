"""Day 20：StreamingWindowedAssistant + 里程碑验收（全部离线 Mock）。"""

from __future__ import annotations

import json

import httpx
import pytest

from chat_session import ChatSession
from streaming_assistant import StreamingWindowedAssistant
from streaming_client import ChatHttpError, StreamingChatClient


SYSTEM = "你是简洁的学习助教，用中文回答。"


def _sse_body(text: str, *, model: str = "gpt-4o-mini") -> bytes:
    chunks: list[dict] = [
        {"id": "c", "choices": [{"index": 0, "delta": {"role": "assistant"}}]},
    ]
    for ch in text:
        chunks.append(
            {"id": "c", "choices": [{"index": 0, "delta": {"content": ch}}]}
        )
    chunks.append(
        {
            "id": "c",
            "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
    )
    parts = [f"data: {json.dumps(obj, ensure_ascii=False)}\n\n" for obj in chunks]
    parts.append("data: [DONE]\n\n")
    return "".join(parts).encode("utf-8")


def _make_client(handler) -> StreamingChatClient:
    return StreamingChatClient(
        "https://api.test/v1",
        "sk-test",
        model="gpt-4o-mini",
        transport=httpx.MockTransport(handler),
    )


def test_ask_stream_and_ask_join() -> None:
    captured: list[list] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        assert body.get("stream") is True
        captured.append(body["messages"])
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=_sse_body("你好"),
        )

    with _make_client(handler) as client:
        bot = StreamingWindowedAssistant(client, system_prompt=SYSTEM, max_turns=3)
        parts = list(bot.ask_stream("嗨"))
        assert "".join(parts) == "你好"
        assert bot.ask("第二问") == "你好"

    assert captured[0][0] == {"role": "system", "content": SYSTEM}
    assert captured[0][1] == {"role": "user", "content": "嗨"}
    assert captured[1][1] == {"role": "user", "content": "嗨"}
    assert captured[1][2] == {"role": "assistant", "content": "你好"}
    assert captured[1][3] == {"role": "user", "content": "第二问"}


def test_sliding_window_keeps_recent_turns() -> None:
    captured: list[list] = []
    n = {"i": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        captured.append(body["messages"])
        n["i"] += 1
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=_sse_body(f"r{n['i']}"),
        )

    with _make_client(handler) as client:
        bot = StreamingWindowedAssistant(client, system_prompt=SYSTEM, max_turns=2)
        bot.ask("t1")
        bot.ask("t2")
        bot.ask("t3")  # 请求仍可带齐前 2 轮；写入后再裁掉 t1
        assert [(m.role, m.content) for m in bot.history()] == [
            ("user", "t2"),
            ("assistant", "r2"),
            ("user", "t3"),
            ("assistant", "r3"),
        ]
        bot.ask("t4")  # 第 4 次请求起，最早轮 t1 已不在

        fourth = captured[3]
        assert fourth[0]["role"] == "system"
        roles_contents = [(m["role"], m["content"]) for m in fourth[1:]]
        assert roles_contents == [
            ("user", "t2"),
            ("assistant", "r2"),
            ("user", "t3"),
            ("assistant", "r3"),
            ("user", "t4"),
        ]



def test_reset_and_empty_user() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=_sse_body("ok"),
        )

    with _make_client(handler) as client:
        bot = StreamingWindowedAssistant(client, system_prompt=SYSTEM)
        with pytest.raises(ValueError, match="empty user_text"):
            bot.ask("  ")
        bot.ask("hi")
        assert len(bot.history()) == 2
        bot.reset()
        assert bot.history() == []


def test_stream_error_does_not_pollute_history() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    with _make_client(handler) as client:
        bot = StreamingWindowedAssistant(client, system_prompt=SYSTEM)
        with pytest.raises(ChatHttpError):
            bot.ask("会失败")
        assert bot.history() == []


def test_session_commands_still_work() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=_sse_body("回"),
        )

    with _make_client(handler) as client:
        bot = StreamingWindowedAssistant(client, system_prompt=SYSTEM)
        session = ChatSession(bot)
        assert session.handle_line("/help").kind == "system"
        r = session.handle_line("你好")
        assert r.kind == "assistant" and r.message == "回"
        assert session.handle_line("/reset").message == "已清空对话历史。"
        assert session.handle_line("/history").message == "当前没有历史消息。"
        assert session.handle_line("/exit").should_exit is True


def test_constructor_validation() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_sse_body("x"))

    with _make_client(handler) as client:
        with pytest.raises(ValueError, match="empty system_prompt"):
            StreamingWindowedAssistant(client, system_prompt="  ")
        with pytest.raises(ValueError, match="max_turns"):
            StreamingWindowedAssistant(client, system_prompt=SYSTEM, max_turns=0)
