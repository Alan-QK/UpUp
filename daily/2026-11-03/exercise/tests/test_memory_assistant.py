"""Day 65 测试：带记忆助理（跨两次运行）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from memory_assistant import (
    ACTION_SKIP,
    ACTION_WRITE,
    DEFAULT_USER_ID,
    KIND_PREFERENCE,
    MEMORY_MARKER,
    REQUIRED_REPORT_SECTIONS,
    FileMemoryStore,
    MemoryAssistant,
    build_mock_reply,
    decide_write,
    mock_embed,
    render_memory_assistant_report,
    run_cross_session_demo,
)


def test_decide_write_basics() -> None:
    assert decide_write("你好").action == ACTION_SKIP
    assert decide_write("我的密码是 Secret123").reason == "sensitive"
    d = decide_write("请记住：以后都用中文回答我")
    assert d.action == ACTION_WRITE
    pref = decide_write("我喜欢深色主题")
    assert pref.action == ACTION_WRITE
    assert pref.kind == KIND_PREFERENCE


def test_file_store_persist_and_reload(tmp_path: Path) -> None:
    path = tmp_path / "mem.json"
    store = FileMemoryStore(path)
    item = store.upsert(
        user_id="u-a",
        text="我喜欢深色主题，少一点动画",
        kind=KIND_PREFERENCE,
        memory_id="m1",
    )
    assert item.id == "m1"
    assert path.exists()
    assert store.size("u-a") == 1

    # 新实例从磁盘加载
    store2 = FileMemoryStore(path)
    assert store2.size("u-a") == 1
    assert store2.list_user("u-a")[0].text.startswith("我喜欢深色")

    hits = store2.search("界面主题建议", user_id="u-a", top_k=2)
    assert len(hits) >= 1
    assert "深色" in hits[0].item.text


def test_user_isolation(tmp_path: Path) -> None:
    path = tmp_path / "iso.json"
    store = FileMemoryStore(path)
    store.upsert(user_id="u-a", text="我喜欢 TypeScript", kind=KIND_PREFERENCE)
    store.upsert(user_id="u-b", text="我喜欢 Go 语言", kind=KIND_PREFERENCE)
    hits_a = store.search("编程语言偏好", user_id="u-a", top_k=3, min_score=0.01)
    assert all(h.item.user_id == "u-a" for h in hits_a)
    assert store.size("u-b") == 1


def test_assistant_write_and_skip(tmp_path: Path) -> None:
    path = tmp_path / "asst.json"
    bot = MemoryAssistant(path, user_id=DEFAULT_USER_ID)
    r1 = bot.handle_turn("你好")
    assert r1.decision.action == ACTION_SKIP
    assert r1.wrote is None
    assert "还没有关于你的长期记忆" in r1.reply

    r2 = bot.handle_turn("我喜欢深色主题，少一点动画")
    assert r2.decision.action == ACTION_WRITE
    assert r2.wrote is not None
    assert bot.stats().store_size == 1
    assert bot.stats().write_count == 1

    r3 = bot.handle_turn("我的密码是 Secret123")
    assert r3.decision.reason == "sensitive"
    assert r3.wrote is None


def test_ask_requires_confirm(tmp_path: Path) -> None:
    path = tmp_path / "ask.json"
    rejected = MemoryAssistant(path, user_id="u1", confirm_fn=lambda _t, _r: False)
    r = rejected.handle_turn("我可能更喜欢浅色，不确定")
    assert r.decision.action == "ask"
    assert r.wrote is None
    assert rejected.stats().ask_count == 1
    assert rejected.stats().ask_accepted == 0

    accepted = MemoryAssistant(path, user_id="u1", confirm_fn=lambda _t, _r: True)
    r2 = accepted.handle_turn("我可能更喜欢浅色，不确定")
    assert r2.wrote is not None
    assert accepted.stats().ask_accepted == 1


def test_cross_session_remembers(tmp_path: Path) -> None:
    path = tmp_path / "cross.json"
    results1, results2, stats = run_cross_session_demo(path)

    assert len(results1) == 6
    assert len(results2) == 2
    assert path.exists()

    # 会话 1：寒暄/敏感/一次性任务不写；显式记住、偏好、事实要写
    actions = [r.decision.action for r in results1]
    reasons = [r.decision.reason for r in results1]
    assert reasons[0] == "ephemeral"
    assert reasons[1] == "explicit_remember"
    assert reasons[2] == "preference_signal"
    assert reasons[3] == "fact_signal"
    assert reasons[4] == "sensitive"
    assert reasons[5] == "no_signal"
    assert actions.count(ACTION_WRITE) >= 3

    # 会话 2：新实例仍能在回复里提到偏好
    theme_reply = results2[0].reply
    lang_reply = results2[1].reply
    assert len(results2[0].recalled) >= 1
    assert "深色" in theme_reply or "主题" in theme_reply or "动画" in theme_reply
    assert "中文" in lang_reply or len(results2[1].recalled) >= 1

    assert stats.store_size >= 3
    assert stats.turns == 8
    assert MEMORY_MARKER in (results2[0].context_block or "")


def test_build_mock_reply_shapes(tmp_path: Path) -> None:
    empty = build_mock_reply("你好", [])
    assert "还没有关于你的长期记忆" in empty

    store = FileMemoryStore(tmp_path / "reply.json")
    item = store.upsert(
        user_id="u",
        text="回答请用中文",
        kind=KIND_PREFERENCE,
        memory_id="p1",
    )
    from memory_assistant import ScoredMemory

    filled = build_mock_reply("语言？", [ScoredMemory(item=item, score=0.9)])
    assert "根据我记得的偏好" in filled
    assert "中文" in filled


def test_report_sections(tmp_path: Path) -> None:
    path = tmp_path / "rep.json"
    r1, r2, stats = run_cross_session_demo(path)
    report = render_memory_assistant_report(r1, r2, stats)
    for section in REQUIRED_REPORT_SECTIONS:
        assert f"## {section}" in report
    assert "会话 1" in report or "写入" in report
    assert str(stats.store_size) in report


def test_mock_embed_stable() -> None:
    a = mock_embed("深色主题")
    b = mock_embed("深色主题")
    assert a == b
    assert len(a) == 32


def test_empty_user_id_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        MemoryAssistant(tmp_path / "x.json", user_id="  ")
