"""Day 45：双工具 Agent 周挑战。"""

from __future__ import annotations

import json

import pytest

from dual_agent import (
    AgentResult,
    HeuristicChat,
    extract_expression,
    extract_timezone,
    last_user_content,
    needs_calculate,
    needs_current_time,
    plan_tool_calls,
    render_agent_markdown,
    run_dual_agent,
    synthesize_answer,
    tool_names_from_messages,
)
from roundtrip import ScriptedChat
from toolkit import DEMO_TIME_UTC, DUAL_TOOL_NAMES, dual_toolkit


def test_dual_toolkit_order() -> None:
    tools = dual_toolkit()
    names = [item["function"]["name"] for item in tools]
    assert names == list(DUAL_TOOL_NAMES)
    assert names == ["get_current_time", "calculate"]


def test_last_user_content() -> None:
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "第一问"},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "第二问"},
    ]
    assert last_user_content(messages) == "第二问"
    with pytest.raises(ValueError, match="list"):
        last_user_content("bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="no user"):
        last_user_content([{"role": "system", "content": "x"}])


def test_needs_heuristics() -> None:
    assert needs_current_time("现在几点了？") is True
    assert needs_current_time("UTC timezone please") is True
    assert needs_current_time("随便聊聊") is False
    assert needs_current_time("   ") is False

    assert needs_calculate("帮我算一下 1+2") is True
    assert needs_calculate("3*4+5") is True
    assert needs_calculate("今天天气如何") is False


def test_extract_expression_and_timezone() -> None:
    assert extract_expression("帮我算一下 12*(3+4)") == "12*(3+4)"
    assert extract_expression("请计算 8/2") == "8/2"
    assert extract_expression("结果是 3 + 4 对吗") == "3+4"
    assert extract_expression("你好") is None

    assert extract_timezone("现在 UTC 几点") == "UTC"
    assert extract_timezone("Asia/Shanghai 的时间") == "Asia/Shanghai"
    assert extract_timezone("上海现在几点") == "Asia/Shanghai"
    assert extract_timezone("随便问问") == "UTC"


def test_plan_tool_calls_variants() -> None:
    only_time = plan_tool_calls("现在 UTC 几点？")
    assert len(only_time) == 1
    assert only_time[0]["id"] == "call_time"
    assert only_time[0]["function"]["name"] == "get_current_time"
    assert json.loads(only_time[0]["function"]["arguments"]) == {"timezone": "UTC"}

    only_calc = plan_tool_calls("帮我算一下 12*(3+4)")
    assert len(only_calc) == 1
    assert only_calc[0]["id"] == "call_calc"
    assert only_calc[0]["function"]["name"] == "calculate"
    assert json.loads(only_calc[0]["function"]["arguments"]) == {
        "expression": "12*(3+4)"
    }

    both = plan_tool_calls("现在 Asia/Shanghai 几点？再帮我算一下 3+4")
    assert [c["function"]["name"] for c in both] == [
        "get_current_time",
        "calculate",
    ]
    assert plan_tool_calls("你好呀") == []


def test_synthesize_answer() -> None:
    tools = [
        {
            "role": "tool",
            "tool_call_id": "call_time",
            "content": json.dumps(
                {"timezone": "UTC", "datetime": DEMO_TIME_UTC},
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        },
        {
            "role": "tool",
            "tool_call_id": "call_calc",
            "content": json.dumps(
                {"expression": "3+4", "result": 7},
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        },
    ]
    text = synthesize_answer("x", tools)
    assert "UTC 当前时间：" + DEMO_TIME_UTC in text
    assert "3+4 = 7" in text
    assert "；" in text

    err = synthesize_answer("x", [{"role": "tool", "tool_call_id": "c", "content": "ERROR: boom"}])
    assert err.startswith("工具失败：")


def test_run_dual_agent_calculate() -> None:
    result = run_dual_agent("帮我算一下 12*(3+4)")
    assert isinstance(result, AgentResult)
    assert result.used_tools is True
    assert result.tool_names == ["calculate"]
    assert "12*(3+4) = 84" in result.final_content
    assert result.messages[0]["role"] == "system"
    assert result.messages[1]["role"] == "user"


def test_run_dual_agent_time() -> None:
    result = run_dual_agent("现在 UTC 几点？")
    assert result.used_tools is True
    assert result.tool_names == ["get_current_time"]
    assert DEMO_TIME_UTC in result.final_content


def test_run_dual_agent_both_and_chat() -> None:
    both = run_dual_agent("现在 Asia/Shanghai 几点？再帮我算一下 3+4")
    assert both.used_tools is True
    assert both.tool_names == ["get_current_time", "calculate"]
    assert "Asia/Shanghai 当前时间：" in both.final_content
    assert "3+4 = 7" in both.final_content

    # 第二次请求应已带 tool 消息
    # HeuristicChat 内部：两轮；messages 末尾是最终 assistant
    assert both.messages[-1]["role"] == "assistant"
    assert both.messages[-1].get("tool_calls") in (None, [])
    tool_roles = [m["role"] for m in both.messages if m["role"] == "tool"]
    assert len(tool_roles) == 2

    chat = run_dual_agent("你好呀")
    assert chat.used_tools is False
    assert chat.tool_names == []
    assert "双工具助手" in chat.final_content


def test_scripted_chat_injection_and_markdown() -> None:
    first = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_calc",
                "type": "function",
                "function": {
                    "name": "calculate",
                    "arguments": '{"expression":"2+2"}',
                },
            }
        ],
    }
    second = {"role": "assistant", "content": "二加二等于四。"}
    chat = ScriptedChat([first, second])
    result = run_dual_agent("随便", chat=chat)
    assert result.final_content == "二加二等于四。"
    assert result.tool_names == ["calculate"]
    assert tool_names_from_messages(result.messages) == ["calculate"]

    md = render_agent_markdown(result)
    lines = md.splitlines()
    assert lines[0] == "# Dual Tool Agent"
    assert "used_tools：yes" in lines
    assert "tools：calculate" in lines
    assert "二加二等于四。" in lines
