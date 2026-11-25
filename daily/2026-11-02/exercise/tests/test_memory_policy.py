"""Day 64 测试：记忆写入策略。"""

from __future__ import annotations

import pytest

from memory_policy import (
    ACTION_ASK,
    ACTION_SKIP,
    ACTION_WRITE,
    KIND_FACT,
    KIND_NONE,
    KIND_NOTE,
    KIND_PREFERENCE,
    REQUIRED_REPORT_SECTIONS,
    ROLE_ASSISTANT,
    ROLE_USER,
    build_demo_utterances,
    contains_sensitive,
    decide_batch,
    decide_write,
    filter_writable,
    normalize_candidate,
    render_memory_policy_report,
    run_demo_policy,
    summarize_decisions,
)


def test_normalize_candidate() -> None:
    assert normalize_candidate("  你好   世界  ") == "你好 世界"
    with pytest.raises(TypeError):
        normalize_candidate(123)  # type: ignore[arg-type]


def test_contains_sensitive() -> None:
    assert contains_sensitive("我的密码是 abc") is True
    assert contains_sensitive("api_key=sk-abcdefghijklmn") is True
    assert contains_sensitive("我喜欢深色主题") is False
    with pytest.raises(TypeError):
        contains_sensitive(None)  # type: ignore[arg-type]


def test_skip_non_user_and_short() -> None:
    d = decide_write("请记住我喜欢 TypeScript", role=ROLE_ASSISTANT)
    assert d.action == ACTION_SKIP
    assert d.reason == "non_user_role"
    assert d.kind == KIND_NONE

    short = decide_write("a")
    assert short.action == ACTION_SKIP
    assert short.reason == "too_short"


def test_skip_sensitive_and_forget() -> None:
    s = decide_write("我的密码是 Secret123")
    assert s.action == ACTION_SKIP
    assert s.reason == "sensitive"

    f = decide_write("不要记住刚才说的话")
    assert f.action == ACTION_SKIP
    assert f.reason == "explicit_forget"


def test_explicit_remember_write() -> None:
    d = decide_write("请记住：以后都用中文回答我")
    assert d.action == ACTION_WRITE
    assert d.reason == "explicit_remember"
    assert d.kind in {KIND_NOTE, KIND_PREFERENCE}
    assert d.confidence == pytest.approx(0.95)
    assert "中文" in d.normalized_text

    pref = decide_write("请记住我喜欢深色主题")
    assert pref.action == ACTION_WRITE
    assert pref.kind == KIND_PREFERENCE


def test_ephemeral_skip() -> None:
    d = decide_write("谢谢")
    assert d.action == ACTION_SKIP
    assert d.reason == "ephemeral"


def test_preference_write_and_ask() -> None:
    w = decide_write("我喜欢深色主题，少一点动画")
    assert w.action == ACTION_WRITE
    assert w.kind == KIND_PREFERENCE
    assert w.reason == "preference_signal"
    assert w.confidence == pytest.approx(0.85)

    a = decide_write("我可能更喜欢浅色，不确定")
    assert a.action == ACTION_ASK
    assert a.kind == KIND_PREFERENCE
    assert a.reason == "preference_hedged"
    assert a.confidence == pytest.approx(0.55)


def test_fact_write_and_default_skip() -> None:
    f = decide_write("我叫小凯，是一名前端工程师")
    assert f.action == ACTION_WRITE
    assert f.kind == KIND_FACT
    assert f.reason == "fact_signal"

    one_off = decide_write("帮我看看这段按钮样式怎么改")
    assert one_off.action == ACTION_SKIP
    assert one_off.reason == "no_signal"


def test_decide_batch_and_filter() -> None:
    messages = [
        (ROLE_USER, "你好"),
        (ROLE_USER, "我喜欢 TypeScript"),
        (ROLE_ASSISTANT, "收到"),
    ]
    decisions = decide_batch(messages)
    assert len(decisions) == 3
    writable = filter_writable(decisions)
    assert len(writable) == 1
    assert writable[0].kind == KIND_PREFERENCE

    with pytest.raises(TypeError):
        decide_batch("nope")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        decide_batch([(ROLE_USER,)])  # type: ignore[list-item]


def test_summarize_and_demo_report() -> None:
    utterances = build_demo_utterances()
    assert len(utterances) == 10
    decisions, stats = run_demo_policy()
    assert stats.total == 10
    assert stats.write_count + stats.skip_count + stats.ask_count == 10
    assert stats.write_count >= 3
    assert stats.ask_count >= 1
    assert stats.skip_count >= 4

    again = summarize_decisions(decisions)
    assert again.write_count == stats.write_count

    report = render_memory_policy_report(decisions, stats)
    for section in REQUIRED_REPORT_SECTIONS:
        assert f"## {section}" in report
    assert "WRITE" in report or "write" in report.lower() or "WRITE：" in report


def test_invalid_role_and_decision_validation() -> None:
    with pytest.raises(ValueError):
        decide_write("我喜欢 Go", role="robot")
    with pytest.raises(TypeError):
        decide_write(123)  # type: ignore[arg-type]
