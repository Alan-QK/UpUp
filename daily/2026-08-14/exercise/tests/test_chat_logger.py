"""Day 19：结构化日志与脱敏。"""

from __future__ import annotations

import io
import json
from datetime import datetime, timedelta, timezone

import pytest

from chat_logger import (
    StructuredLogger,
    mask_value,
    preview_text,
    sanitize_fields,
    should_mask_key,
)


FIXED = datetime(2026, 8, 14, 2, 0, 0, tzinfo=timezone.utc)


def test_should_mask_key() -> None:
    assert should_mask_key("api_key") is True
    assert should_mask_key("API_KEY") is True
    assert should_mask_key("authorization") is True
    assert should_mask_key("password") is True
    assert should_mask_key("secret") is True
    assert should_mask_key("token") is True
    assert should_mask_key("openai_api_key") is True
    assert should_mask_key("refresh_token") is True
    assert should_mask_key("db_password") is True
    assert should_mask_key("client_secret") is True
    assert should_mask_key("model") is False
    assert should_mask_key("session_id") is False
    assert should_mask_key("user_text") is False


def test_mask_value() -> None:
    assert mask_value("") == "***"
    assert mask_value("short") == "***"
    assert mask_value("1234567") == "***"  # 7 <= 3+4
    assert mask_value("sk-abcdefghijklmnop") == "sk-***mnop"
    assert mask_value("abcdefghij", head=2, tail=2) == "ab***ij"


def test_preview_text() -> None:
    assert preview_text("  hi  ") == "hi"
    assert preview_text("x" * 40) == "x" * 40
    assert preview_text("x" * 41) == ("x" * 40) + "..."


def test_sanitize_fields_and_extra_keys() -> None:
    raw = {
        "model": "m1",
        "api_key": "sk-abcdefghijklmnop",
        "count": 3,
        "my_custom": "should-hide",
        "ok": True,
    }
    out = sanitize_fields(raw, extra_secret_keys=frozenset({"my_custom"}))
    assert out["model"] == "m1"
    assert out["api_key"] == "sk-***mnop"
    assert out["count"] == 3
    assert out["my_custom"] == "sho***hide"
    assert out["ok"] is True
    # 不修改原 dict
    assert raw["api_key"] == "sk-abcdefghijklmnop"


def test_log_writes_one_json_line() -> None:
    buf = io.StringIO()
    ticks = iter([FIXED])

    logger = StructuredLogger(sink=buf, clock=lambda: next(ticks))
    logger.log("info", "cli.start", session_id="s1", api_key="sk-abcdefghijklmnop")

    text = buf.getvalue()
    assert text.endswith("\n")
    assert text.count("\n") == 1
    payload = json.loads(text.strip())
    assert payload == {
        "ts": FIXED.isoformat(),
        "level": "info",
        "event": "cli.start",
        "session_id": "s1",
        "api_key": "sk-***mnop",
    }


def test_log_chat_turn_success() -> None:
    buf = io.StringIO()
    t0 = FIXED
    t1 = FIXED + timedelta(milliseconds=25)
    ticks = iter([t0, t0, t1])  # request ts, start latency, end latency

    logger = StructuredLogger(sink=buf, clock=lambda: next(ticks))

    reply = logger.log_chat_turn(
        session_id="s1",
        model="fake",
        user_text="  什么是 Agent？  ",
        complete=lambda: "Agent 是能调用工具完成任务的 LLM 系统。",
    )
    assert "工具" in reply

    lines = [json.loads(line) for line in buf.getvalue().splitlines()]
    assert len(lines) == 2
    req, resp = lines
    assert req["event"] == "chat.request"
    assert req["level"] == "info"
    assert req["session_id"] == "s1"
    assert req["model"] == "fake"
    assert req["user_preview"] == "什么是 Agent？"
    assert req["user_chars"] == len("什么是 Agent？")
    assert "ts" in req

    assert resp["event"] == "chat.response"
    assert resp["session_id"] == "s1"
    assert resp["model"] == "fake"
    assert resp["latency_ms"] == 25
    assert resp["reply_chars"] == len(reply)
    assert resp["reply_preview"] == preview_text(reply)


def test_log_chat_turn_error_reraise() -> None:
    buf = io.StringIO()
    t0 = FIXED
    t1 = FIXED + timedelta(milliseconds=10)
    ticks = iter([t0, t0, t1])

    logger = StructuredLogger(sink=buf, clock=lambda: next(ticks))

    class Boom(RuntimeError):
        pass

    with pytest.raises(Boom, match="provider down"):
        logger.log_chat_turn(
            session_id="s2",
            model="m",
            user_text="hi",
            complete=lambda: (_ for _ in ()).throw(Boom("provider down")),
        )

    lines = [json.loads(line) for line in buf.getvalue().splitlines()]
    assert len(lines) == 2
    assert lines[0]["event"] == "chat.request"
    err = lines[1]
    assert err["event"] == "chat.error"
    assert err["level"] == "error"
    assert err["error_type"] == "Boom"
    assert err["error_message"] == "provider down"
    assert err["session_id"] == "s2"
    assert err["model"] == "m"


def test_error_message_truncated() -> None:
    buf = io.StringIO()
    ticks = iter([FIXED, FIXED, FIXED])
    logger = StructuredLogger(sink=buf, clock=lambda: next(ticks))
    long_msg = "x" * 200

    with pytest.raises(ValueError):
        logger.log_chat_turn(
            session_id="s",
            model="m",
            user_text="q",
            complete=lambda: (_ for _ in ()).throw(ValueError(long_msg)),
        )

    err = json.loads(buf.getvalue().splitlines()[-1])
    assert err["error_message"] == ("x" * 120) + "..."
