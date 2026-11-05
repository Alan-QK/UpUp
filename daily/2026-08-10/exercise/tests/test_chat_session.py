"""Day 15：ChatSession 测试（全部离线 Mock）。"""

from __future__ import annotations

import json

import httpx
import pytest

from chat_client import ChatClient, ChatClientError, ChatHttpError
from chat_session import ChatSession, SessionReply
from persona_assistant import PersonaAssistant


SYSTEM = "你是简洁的学习助教，用中文回答。"


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


def _make_session(handler) -> tuple[ChatClient, ChatSession]:
    transport = httpx.MockTransport(handler)
    client = ChatClient(
        "https://api.test/v1",
        "sk-test",
        model="gpt-4o-mini",
        transport=transport,
    )
    bot = PersonaAssistant(client, system_prompt=SYSTEM)
    return client, ChatSession(bot)


def test_empty_line_ignored() -> None:
    called = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["n"] += 1
        return httpx.Response(200, json=_ok_payload("x"))

    client, session = _make_session(handler)
    with client:
        result = session.handle_line("   \n")
    assert result == SessionReply(kind="system", message="（空输入已忽略）")
    assert called["n"] == 0


def test_help_command() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_ok_payload("x"))

    client, session = _make_session(handler)
    with client:
        result = session.handle_line("/help")
    assert result.kind == "system"
    assert result.should_exit is False
    assert "/reset" in result.message
    assert "/exit" in result.message


def test_exit_and_quit() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_ok_payload("x"))

    client, session = _make_session(handler)
    with client:
        r1 = session.handle_line("/exit")
        r2 = session.handle_line("/QUIT")
    assert r1.should_exit is True and r1.kind == "exit"
    assert r2.should_exit is True and r2.kind == "exit"
    assert r1.message == "再见。"


def test_unknown_command() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_ok_payload("x"))

    client, session = _make_session(handler)
    with client:
        result = session.handle_line("/foo")
    assert result.kind == "system"
    assert result.should_exit is False
    assert "未知命令：/foo" in result.message


def test_chat_and_multi_turn() -> None:
    captured: list[list] = []
    replies = iter(["你好呀", "第二轮记得你"])

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        captured.append(body["messages"])
        return httpx.Response(200, json=_ok_payload(next(replies)))

    client, session = _make_session(handler)
    with client:
        r1 = session.handle_line("你好")
        r2 = session.handle_line("还记得我吗？")

    assert r1 == SessionReply(kind="assistant", message="你好呀")
    assert r2.message == "第二轮记得你"
    assert captured[1][0]["role"] == "system"
    assert captured[1][1] == {"role": "user", "content": "你好"}
    assert captured[1][2] == {"role": "assistant", "content": "你好呀"}
    assert captured[1][3] == {"role": "user", "content": "还记得我吗？"}


def test_reset_clears_history() -> None:
    captured: list[list] = []
    n = {"i": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        captured.append(body["messages"])
        n["i"] += 1
        return httpx.Response(200, json=_ok_payload(f"r{n['i']}"))

    client, session = _make_session(handler)
    with client:
        session.handle_line("旧话题")
        reset = session.handle_line("/reset")
        hist = session.handle_line("/history")
        session.handle_line("新话题")

    assert reset == SessionReply(kind="system", message="已清空对话历史。")
    assert hist.message == "当前没有历史消息。"
    assert captured[1] == [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "新话题"},
    ]


def test_history_format_and_truncate() -> None:
    long_text = "字" * 100

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_ok_payload(long_text))

    client, session = _make_session(handler)
    with client:
        session.handle_line("短问")
        result = session.handle_line("/history")

    assert result.kind == "system"
    assert "当前历史共 2 条消息：" in result.message
    assert "[user] 短问" in result.message
    assert "[assistant] " + ("字" * 80) + "..." in result.message
    assert "字" * 100 not in result.message


def test_chat_client_error_becomes_system_reply() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    client, session = _make_session(handler)
    with client:
        result = session.handle_line("会失败")

    assert result.kind == "system"
    assert result.should_exit is False
    assert result.message.startswith("调用失败：")
    assert "500" in result.message


def test_command_case_insensitive_reset() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_ok_payload("ok"))

    client, session = _make_session(handler)
    with client:
        session.handle_line("hi")
        result = session.handle_line("/Reset")
        empty = session.handle_line("/history")

    assert result.message == "已清空对话历史。"
    assert empty.message == "当前没有历史消息。"


def test_http_error_type_is_chat_client_error() -> None:
    """确保练习依赖的异常基类仍可用（防回归）。"""
    assert issubclass(ChatHttpError, ChatClientError)
