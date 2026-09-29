"""Day 12：PersonaAssistant 测试（全部离线 Mock）。"""

from __future__ import annotations

import json

import httpx
import pytest

from chat_client import ChatClient, ChatMessage
from persona_assistant import PersonaAssistant


SYSTEM = "你是严谨的代码审查助手，回答简洁，用中文。"


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
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        },
    }


def _make_client(handler) -> ChatClient:
    transport = httpx.MockTransport(handler)
    return ChatClient(
        "https://api.test/v1",
        "sk-test",
        model="gpt-4o-mini",
        transport=transport,
    )


def test_empty_system_prompt_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_ok_payload("x"))

    with _make_client(handler) as client:
        with pytest.raises(ValueError, match="empty system_prompt"):
            PersonaAssistant(client, system_prompt="   ")


def test_empty_user_text_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_ok_payload("x"))

    with _make_client(handler) as client:
        bot = PersonaAssistant(client, system_prompt=SYSTEM)
        with pytest.raises(ValueError, match="empty user_text"):
            bot.ask("  \n")


def test_first_ask_sends_system_and_user() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        captured["messages"] = body["messages"]
        return httpx.Response(200, json=_ok_payload("首轮回复"))

    with _make_client(handler) as client:
        bot = PersonaAssistant(client, system_prompt=SYSTEM)
        reply = bot.ask("这段代码有什么问题？")

    assert reply == "首轮回复"
    assert captured["messages"] == [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "这段代码有什么问题？"},
    ]
    hist = bot.history()
    assert hist == [
        ChatMessage(role="user", content="这段代码有什么问题？"),
        ChatMessage(role="assistant", content="首轮回复"),
    ]


def test_second_ask_includes_prior_turns() -> None:
    captured: list[list] = []
    replies = iter(["先这样改", "再补测试"])

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        captured.append(body["messages"])
        return httpx.Response(200, json=_ok_payload(next(replies)))

    with _make_client(handler) as client:
        bot = PersonaAssistant(client, system_prompt=SYSTEM)
        bot.ask("第一问")
        bot.ask("第二问", temperature=0.1)

    assert captured[0][0] == {"role": "system", "content": SYSTEM}
    assert captured[1] == [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "第一问"},
        {"role": "assistant", "content": "先这样改"},
        {"role": "user", "content": "第二问"},
    ]
    assert [m.role for m in bot.history()] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]


def test_reset_clears_history_keeps_persona() -> None:
    captured: list[list] = []
    n = {"i": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        captured.append(body["messages"])
        n["i"] += 1
        return httpx.Response(200, json=_ok_payload(f"r{n['i']}"))

    with _make_client(handler) as client:
        bot = PersonaAssistant(client, system_prompt=f"  {SYSTEM}  ")
        bot.ask("旧话题")
        bot.reset()
        assert bot.history() == []
        bot.ask("新话题")

    assert captured[1] == [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "新话题"},
    ]


def test_history_returns_copy() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_ok_payload("ok"))

    with _make_client(handler) as client:
        bot = PersonaAssistant(client, system_prompt=SYSTEM)
        bot.ask("hi")
        hist = bot.history()
        hist.clear()
        assert len(bot.history()) == 2
