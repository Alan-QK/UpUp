"""Day 16：滑动窗口与 WindowedAssistant 测试（全部离线 Mock）。"""

from __future__ import annotations

import json

import httpx
import pytest

from chat_client import ChatClient, ChatMessage
from history_window import WindowedAssistant, count_turns, sliding_window


SYSTEM = "你是简洁助教，回答用中文。"


def _msg(role: str, content: str) -> ChatMessage:
    return ChatMessage(role=role, content=content)


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


def test_sliding_window_rejects_bad_max_turns() -> None:
    with pytest.raises(ValueError, match="max_turns must be >= 1"):
        sliding_window([], max_turns=0)
    with pytest.raises(ValueError, match="max_turns must be >= 1"):
        sliding_window([_msg("user", "a"), _msg("assistant", "b")], max_turns=-1)


def test_sliding_window_empty_and_under_limit() -> None:
    assert sliding_window([], max_turns=2) == []
    hist = [
        _msg("user", "u1"),
        _msg("assistant", "a1"),
        _msg("user", "u2"),
        _msg("assistant", "a2"),
    ]
    assert sliding_window(hist, max_turns=3) == hist
    assert sliding_window(hist, max_turns=2) == hist


def test_sliding_window_keeps_last_turns_only() -> None:
    hist = [
        _msg("user", "u1"),
        _msg("assistant", "a1"),
        _msg("user", "u2"),
        _msg("assistant", "a2"),
        _msg("user", "u3"),
        _msg("assistant", "a3"),
    ]
    got = sliding_window(hist, max_turns=2)
    assert [(m.role, m.content) for m in got] == [
        ("user", "u2"),
        ("assistant", "a2"),
        ("user", "u3"),
        ("assistant", "a3"),
    ]
    # 不修改入参
    assert len(hist) == 6


def test_sliding_window_ignores_system_and_orphans() -> None:
    hist = [
        _msg("system", "should-ignore"),
        _msg("assistant", "orphan-a"),
        _msg("user", "u1"),
        _msg("assistant", "a1"),
        _msg("user", "lonely-user"),
        _msg("user", "u2"),
        _msg("assistant", "a2"),
    ]
    got = sliding_window(hist, max_turns=1)
    assert [(m.role, m.content) for m in got] == [
        ("user", "u2"),
        ("assistant", "a2"),
    ]
    assert count_turns(hist) == 2


def test_count_turns() -> None:
    assert count_turns([]) == 0
    assert count_turns([_msg("user", "x")]) == 0
    assert (
        count_turns(
            [
                _msg("user", "u1"),
                _msg("assistant", "a1"),
                _msg("user", "u2"),
                _msg("assistant", "a2"),
            ]
        )
        == 2
    )


def test_windowed_assistant_validation() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_ok_payload("x"))

    with _make_client(handler) as client:
        with pytest.raises(ValueError, match="empty system_prompt"):
            WindowedAssistant(client, system_prompt="  ", max_turns=2)
        with pytest.raises(ValueError, match="max_turns must be >= 1"):
            WindowedAssistant(client, system_prompt=SYSTEM, max_turns=0)


def test_window_drops_old_turns_from_request() -> None:
    captured: list[list] = []
    replies = iter(["r1", "r2", "r3"])

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        captured.append(body["messages"])
        return httpx.Response(200, json=_ok_payload(next(replies)))

    with _make_client(handler) as client:
        bot = WindowedAssistant(client, system_prompt=SYSTEM, max_turns=1)
        assert bot.max_turns == 1
        bot.ask("第一问")
        bot.ask("第二问")
        bot.ask("第三问")

    # 第 3 轮请求：system + 第 2 轮完整对话 + 本轮 user（不含第一问）
    assert captured[2] == [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "第二问"},
        {"role": "assistant", "content": "r2"},
        {"role": "user", "content": "第三问"},
    ]
    # 本地历史也被裁成最近 1 轮
    assert [(m.role, m.content) for m in bot.history()] == [
        ("user", "第三问"),
        ("assistant", "r3"),
    ]
    assert count_turns(bot.history()) == 1


def test_window_max_turns_two_drops_on_fourth_request() -> None:
    captured: list[list] = []
    n = {"i": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        captured.append(body["messages"])
        n["i"] += 1
        return httpx.Response(200, json=_ok_payload(f"r{n['i']}"))

    with _make_client(handler) as client:
        bot = WindowedAssistant(client, system_prompt=f"  {SYSTEM}  ", max_turns=2)
        bot.ask("A")
        bot.ask("B")
        bot.ask("C")
        # 第 3 轮结束后本地已裁成 B+C；第 4 轮请求不应再带 A
        bot.ask("D")

    # 第 3 轮请求仍可带 A+B（当时历史正好 2 轮，尚未超窗）
    assert ("user", "A") in [(m["role"], m["content"]) for m in captured[2]]

    roles_contents = [(m["role"], m["content"]) for m in captured[3]]
    assert roles_contents[0] == ("system", SYSTEM)
    assert ("user", "A") not in roles_contents
    assert ("user", "B") in roles_contents
    assert ("assistant", "r2") in roles_contents
    assert ("user", "C") in roles_contents
    assert ("assistant", "r3") in roles_contents
    assert roles_contents[-1] == ("user", "D")


def test_empty_user_and_reset_and_history_copy() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_ok_payload("ok"))

    with _make_client(handler) as client:
        bot = WindowedAssistant(client, system_prompt=SYSTEM, max_turns=2)
        with pytest.raises(ValueError, match="empty user_text"):
            bot.ask("  \n")
        bot.ask("hi")
        bot.reset()
        assert bot.history() == []
        bot.ask("again")
        hist = bot.history()
        hist.clear()
        assert len(bot.history()) == 2
