"""Day 61 测试：增强历史窗口。"""

from __future__ import annotations

import copy

import pytest

from memory_window import (
    REQUIRED_REPORT_SECTIONS,
    ChatTurn,
    SessionMemory,
    apply_enhanced_window,
    build_demo_transcript,
    count_exchange_turns,
    estimate_tokens,
    message_tokens,
    render_window_report,
)


def test_estimate_tokens_empty_and_basic() -> None:
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1  # (4+3)//4 = 1
    assert estimate_tokens("a") == 1
    assert estimate_tokens("abcdefgh") == 2  # (8+3)//4 = 2


def test_estimate_tokens_rejects_non_str() -> None:
    with pytest.raises(TypeError):
        estimate_tokens(123)  # type: ignore[arg-type]


def test_chat_turn_rejects_bad_role() -> None:
    with pytest.raises(ValueError):
        ChatTurn(role="system_prompt", content="x")


def test_count_exchange_turns_ignores_system_and_pinned_orphan() -> None:
    msgs = build_demo_transcript()
    # system + pinned user + 4 完整轮
    assert count_exchange_turns(msgs) == 4


def test_apply_requires_at_least_one_limit() -> None:
    with pytest.raises(ValueError, match="must provide"):
        apply_enhanced_window([ChatTurn(role="user", content="hi")])


def test_apply_rejects_invalid_limits() -> None:
    msg = [ChatTurn(role="user", content="a"), ChatTurn(role="assistant", content="b")]
    with pytest.raises(ValueError):
        apply_enhanced_window(msg, max_turns=0)
    with pytest.raises(ValueError):
        apply_enhanced_window(msg, max_tokens=0)


def test_max_turns_keeps_recent_exchanges_and_system_pinned() -> None:
    msgs = build_demo_transcript()
    snapshot = copy.deepcopy(msgs)
    result = apply_enhanced_window(msgs, max_turns=2)

    # 不修改入参
    assert msgs == snapshot

    roles_contents = [(m.role, m.content, m.pinned) for m in result.messages]
    assert roles_contents[0][0] == "system"
    assert any(m.pinned for m in result.messages)
    assert "我叫小前端。请记住。" in [m.content for m in result.messages]

    # 4 轮里只留最近 2 轮 + 保护项
    assert count_exchange_turns(result.messages) == 2
    assert "短记忆和长期记忆差别？" in [m.content for m in result.messages]
    assert "HITL 呢？" in [m.content for m in result.messages]
    assert "什么是 Agent Loop？" not in [m.content for m in result.messages]
    assert result.stats.dropped_messages >= 2
    assert result.stats.system_kept == 1
    assert result.stats.pinned_kept == 1


def test_max_tokens_drops_older_turns() -> None:
    msgs = [
        ChatTurn(role="system", content="S"),
        ChatTurn(role="user", content="U1" * 20),
        ChatTurn(role="assistant", content="A1" * 20),
        ChatTurn(role="user", content="U2"),
        ChatTurn(role="assistant", content="A2"),
    ]
    # 很小的预算：几乎只能留下 system + 最后一轮短对话
    sys_cost = message_tokens(msgs[0])
    last_cost = message_tokens(msgs[3]) + message_tokens(msgs[4])
    budget = sys_cost + last_cost
    result = apply_enhanced_window(msgs, max_tokens=budget)
    contents = [m.content for m in result.messages]
    assert "S" in contents
    assert "U2" in contents and "A2" in contents
    assert "U1" * 20 not in contents
    assert result.stats.estimated_tokens_kept <= budget


def test_combined_turns_and_tokens() -> None:
    msgs = build_demo_transcript()
    # 先限 3 轮，再把预算压到装不下 3 轮
    loose = apply_enhanced_window(msgs, max_turns=3)
    tight_budget = max(8, loose.stats.estimated_tokens_kept // 2)
    result = apply_enhanced_window(msgs, max_turns=3, max_tokens=tight_budget)
    assert result.stats.kept_messages <= loose.stats.kept_messages
    assert any(m.role == "system" for m in result.messages)
    assert any(m.pinned for m in result.messages)


def test_orphans_dropped_unless_pinned() -> None:
    msgs = [
        ChatTurn(role="system", content="sys"),
        ChatTurn(role="tool", content="tool-output"),
        ChatTurn(role="user", content="lone user"),
        ChatTurn(role="user", content="Q"),
        ChatTurn(role="assistant", content="A"),
    ]
    result = apply_enhanced_window(msgs, max_turns=1)
    contents = [m.content for m in result.messages]
    assert "tool-output" not in contents
    assert "lone user" not in contents
    assert contents == ["sys", "Q", "A"] or (
        contents[0] == "sys" and "Q" in contents and "A" in contents
    )


def test_session_memory_add_exchange_trims() -> None:
    mem = SessionMemory(max_turns=1, system_prompt="助手")
    mem.add_exchange("第一问", "第一答")
    mem.add_exchange("第二问", "第二答")
    hist = mem.history()
    assert any(m.role == "system" for m in hist)
    assert "第二问" in [m.content for m in hist]
    assert "第一问" not in [m.content for m in hist]
    assert mem.last_result() is not None
    assert mem.last_result().stats.dropped_messages >= 2


def test_session_memory_pinned_survives() -> None:
    mem = SessionMemory(max_turns=1, system_prompt="助手")
    mem.add("user", "我的偏好是简洁回答", pinned=True)
    mem.add_exchange("Q1", "A1")
    mem.add_exchange("Q2", "A2")
    contents = [m.content for m in mem.history()]
    assert "我的偏好是简洁回答" in contents
    assert "Q2" in contents
    assert "Q1" not in contents


def test_session_memory_validation() -> None:
    with pytest.raises(ValueError):
        SessionMemory(max_turns=None, max_tokens=None)
    with pytest.raises(ValueError):
        SessionMemory(max_turns=1, system_prompt="   ")
    mem = SessionMemory(max_turns=2, system_prompt="S")
    with pytest.raises(ValueError):
        mem.add("user", "  ")


def test_render_window_report_sections() -> None:
    result = apply_enhanced_window(build_demo_transcript(), max_turns=2)
    text = render_window_report(result)
    for section in REQUIRED_REPORT_SECTIONS:
        assert f"## {section}" in text
    assert "kept:" in text
