"""Day 62 测试：摘要记忆。"""

from __future__ import annotations

import copy

import pytest

from summary_memory import (
    REQUIRED_REPORT_SECTIONS,
    SUMMARY_MARKER,
    ChatTurn,
    SummarizingMemory,
    build_demo_exchanges,
    compact_exchanges,
    default_summarize,
    estimate_tokens,
    format_summary_message,
    is_summary_message,
    render_summary_report,
)


def test_estimate_tokens_empty_and_basic() -> None:
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcdefgh") == 2


def test_estimate_tokens_rejects_non_str() -> None:
    with pytest.raises(TypeError):
        estimate_tokens(123)  # type: ignore[arg-type]


def test_format_summary_message_adds_marker() -> None:
    msg = format_summary_message("已讨论 Loop")
    assert msg.role == "system"
    assert msg.content.startswith(SUMMARY_MARKER)
    assert "已讨论 Loop" in msg.content
    assert is_summary_message(msg)


def test_format_summary_message_rejects_empty() -> None:
    with pytest.raises(ValueError):
        format_summary_message("   ")


def test_default_summarize_fresh_and_rolling() -> None:
    exchanges = [("问A", "答A"), ("问B", "答B")]
    fresh = default_summarize(exchanges, None)
    assert fresh.startswith("对话摘要：")
    assert "用户：问A" in fresh and "助手：答A" in fresh

    rolled = default_summarize([("问C", "答C")], fresh)
    assert fresh in rolled
    assert "近期折叠：" in rolled
    assert "问C" in rolled


def test_default_summarize_rejects_empty() -> None:
    with pytest.raises(ValueError):
        default_summarize([])


def test_compact_no_fold_when_within_limit() -> None:
    exchanges = build_demo_exchanges()[:2]
    snapshot = copy.deepcopy(exchanges)
    result = compact_exchanges(
        exchanges,
        keep_recent_turns=3,
        system_prompt="助手",
    )
    assert exchanges == snapshot
    assert result.folded == []
    assert result.summary_text is None
    assert result.stats.kept_recent_exchanges == 2
    assert result.messages[0] == ChatTurn(role="system", content="助手")
    assert result.messages[1].role == "user"


def test_compact_folds_oldest_and_keeps_recent() -> None:
    exchanges = build_demo_exchanges()  # 5 轮
    result = compact_exchanges(
        exchanges,
        keep_recent_turns=2,
        system_prompt="学习助理",
    )
    assert result.stats.folded_exchanges == 3
    assert result.stats.kept_recent_exchanges == 2
    assert result.summary_text is not None
    assert "我叫小前端" in result.summary_text
    assert "Agent Loop" in result.summary_text

    roles = [m.role for m in result.messages]
    assert roles[0] == "system"
    assert is_summary_message(result.messages[1])
    # 最近两轮原文仍在
    contents = [m.content for m in result.messages]
    assert "短记忆和摘要记忆差别？" in contents
    assert "HITL 呢？" in contents
    assert "什么是 Agent Loop？" not in contents


def test_compact_preserves_previous_summary_when_rolling() -> None:
    first = compact_exchanges(
        build_demo_exchanges()[:3],
        keep_recent_turns=1,
    )
    assert first.summary_text is not None
    second = compact_exchanges(
        [("新问题", "新回答"), ("又一问", "又一答")],
        keep_recent_turns=1,
        previous_summary=first.summary_text,
    )
    assert first.summary_text in (second.summary_text or "")
    assert "新问题" in (second.summary_text or "")
    assert second.stats.folded_exchanges == 1
    assert second.stats.kept_recent_exchanges == 1


def test_compact_validates_params() -> None:
    with pytest.raises(ValueError):
        compact_exchanges([("a", "b")], keep_recent_turns=0)
    with pytest.raises(ValueError):
        compact_exchanges([("a", "b")], keep_recent_turns=1, system_prompt="  ")


def test_custom_summarizer_is_used() -> None:
    def boom(
        exchanges: list[tuple[str, str]], previous_summary: str | None
    ) -> str:
        return f"CUSTOM:{len(exchanges)}:{previous_summary or '-'}"

    result = compact_exchanges(
        [("u1", "a1"), ("u2", "a2"), ("u3", "a3")],
        keep_recent_turns=1,
        summarizer=boom,
    )
    assert result.summary_text == "CUSTOM:2:-"


def test_summarizing_memory_auto_folds() -> None:
    mem = SummarizingMemory(keep_recent_turns=2, system_prompt="助手")
    mem.add_exchange("第一问", "第一答")
    mem.add_exchange("第二问", "第二答")
    assert mem.summary is None
    assert len(mem.exchanges()) == 2

    result = mem.add_exchange("第三问", "第三答")
    assert result.stats.folded_exchanges == 1
    assert mem.summary is not None
    assert "第一问" in mem.summary
    assert len(mem.exchanges()) == 2
    assert "第三问" in [u for u, _ in mem.exchanges()]
    assert "第一问" not in [u for u, _ in mem.exchanges()]

    ctx = mem.context_messages()
    assert ctx[0].content == "助手"
    assert is_summary_message(ctx[1])
    assert any(m.content == "第三问" for m in ctx)


def test_summarizing_memory_rolling_summary_grows() -> None:
    mem = SummarizingMemory(keep_recent_turns=1, system_prompt="S")
    mem.add_exchange("A问", "A答")
    mem.add_exchange("B问", "B答")  # folds A
    first_summary = mem.summary
    assert first_summary is not None
    mem.add_exchange("C问", "C答")  # folds B into previous
    assert first_summary in (mem.summary or "")
    assert "B问" in (mem.summary or "")
    assert len(mem.exchanges()) == 1
    assert mem.exchanges()[0][0] == "C问"


def test_summarizing_memory_validation_and_reset() -> None:
    with pytest.raises(ValueError):
        SummarizingMemory(keep_recent_turns=0)
    with pytest.raises(ValueError):
        SummarizingMemory(keep_recent_turns=1, system_prompt="  ")
    mem = SummarizingMemory(keep_recent_turns=1, system_prompt="S")
    with pytest.raises(ValueError):
        mem.add_exchange("  ", "x")
    mem.add_exchange("q", "a")
    mem.add_exchange("q2", "a2")
    assert mem.summary is not None
    mem.reset()
    assert mem.exchanges() == []
    assert mem.summary is None
    assert mem.last_result() is None


def test_render_summary_report_sections() -> None:
    result = compact_exchanges(
        build_demo_exchanges(),
        keep_recent_turns=2,
        system_prompt="助手",
    )
    text = render_summary_report(result)
    for section in REQUIRED_REPORT_SECTIONS:
        assert f"## {section}" in text
    assert "kept_recent:" in text
