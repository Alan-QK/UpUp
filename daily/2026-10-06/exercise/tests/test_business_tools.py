"""Day 53 测试：自定义业务工具 order_lookup 接入框架。"""

from __future__ import annotations

import json

import pytest

from business_tools import (
    ORDER_DB,
    build_business_agent,
    business_system_prompt,
    order_lookup,
    order_lookup_tool_meta,
    register_business_tools,
    render_extension_checklist,
)
from mini_framework import (
    ERROR_PREFIX,
    STOP_FINAL,
    AgentRunner,
    ScriptedChat,
    build_default_registry,
    tool_from_meta,
)


def _call(call_id: str, name: str, arguments: dict | str) -> dict:
    if isinstance(arguments, dict):
        raw = json.dumps(arguments, ensure_ascii=False)
    else:
        raw = arguments
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": raw},
    }


def test_order_lookup_happy_path() -> None:
    text = order_lookup("ORD-1001")
    assert "ORD-1001" in text
    assert "shipped" in text
    assert "128.00" in text
    assert "CNY" in text
    assert "上海" in text
    assert "机械键盘" in text


def test_order_lookup_normalizes_and_unknown() -> None:
    text = order_lookup("  ORD-1002  ")
    assert "processing" in text
    assert "杭州" in text

    with pytest.raises(ValueError):
        order_lookup("   ")

    with pytest.raises((KeyError, ValueError)) as exc_info:
        order_lookup("ORD-9999")
    assert "ORD-9999" in str(exc_info.value)


def test_order_lookup_tool_meta_shape() -> None:
    meta = order_lookup_tool_meta()
    assert meta["name"] == "order_lookup"
    assert isinstance(meta["description"], str) and meta["description"].strip()
    assert meta["handler"] is order_lookup
    params = meta["parameters"]
    assert params["type"] == "object"
    assert "order_id" in params["properties"]
    assert "order_id" in params["required"]

    tool = tool_from_meta(meta)
    assert tool.name == "order_lookup"


def test_register_business_tools_keeps_builtins() -> None:
    registry = build_default_registry()
    register_business_tools(registry)
    assert registry.names() == ("lookup", "calculate", "order_lookup")
    assert registry.execute("lookup", {"key": "alpha"}) == "7"
    assert "ORD-1003" in registry.execute(
        "order_lookup", {"order_id": "ORD-1003"}
    )
    err = registry.execute("order_lookup", {"order_id": "ORD-0000"})
    assert err.startswith(ERROR_PREFIX)


def test_register_rejects_non_registry() -> None:
    with pytest.raises(TypeError):
        register_business_tools({"nope": True})  # type: ignore[arg-type]


def test_business_system_prompt_mentions_order_tool() -> None:
    registry = register_business_tools(build_default_registry())
    prompt = business_system_prompt(registry)
    assert "order_lookup" in prompt
    assert "lookup" in prompt
    assert "calculate" in prompt


def test_build_business_agent_wires_tool() -> None:
    agent = build_business_agent(name="biz", max_steps=4)
    assert agent.name == "biz"
    assert agent.max_steps == 4
    assert agent.registry.get("order_lookup") is not None
    assert "order_lookup" in agent.system_prompt
    names = [t["function"]["name"] for t in agent.registry.openai_tools()]
    assert names == ["lookup", "calculate", "order_lookup"]


def test_runner_uses_order_lookup() -> None:
    agent = build_business_agent(max_steps=6)
    chat = ScriptedChat(
        [
            {
                "role": "assistant",
                "content": "查单",
                "tool_calls": [
                    _call("c1", "order_lookup", {"order_id": "ORD-1002"})
                ],
            },
            {
                "role": "assistant",
                "content": "订单处理中，合计 59.90 CNY。",
            },
        ]
    )
    result = AgentRunner().run(agent, "查 ORD-1002", chat)
    assert result.stopped_reason == STOP_FINAL
    assert result.steps == 2
    assert result.tool_names_used == ("order_lookup",)
    assert any(
        m.get("role") == "tool" and "processing" in str(m.get("content"))
        for m in chat.calls[1]
    )


def test_runner_can_mix_builtin_and_business() -> None:
    """业务工具与内置工具可在同一次运行中组合。"""
    agent = build_business_agent(max_steps=6)
    chat = ScriptedChat(
        [
            {
                "role": "assistant",
                "content": "查单",
                "tool_calls": [
                    _call("c1", "order_lookup", {"order_id": "ORD-1001"})
                ],
            },
            {
                "role": "assistant",
                "content": "再算运费相关",
                "tool_calls": [
                    _call("c2", "calculate", {"expression": "128/2"})
                ],
            },
            {"role": "assistant", "content": "订单已发货；半价示意 64。"},
        ]
    )
    result = AgentRunner().run(agent, "查 ORD-1001 并演示计算", chat)
    assert result.stopped_reason == STOP_FINAL
    assert result.tool_names_used == ("order_lookup", "calculate")


def test_render_extension_checklist() -> None:
    md = render_extension_checklist()
    assert "# 自定义工具接入清单" in md
    for heading in (
        "## 1. Handler",
        "## 2. Schema",
        "## 3. Register",
        "## 4. Prompt",
        "## 5. Verify",
    ):
        assert heading in md
    # 不应是空壳标题堆砌：每个 section 后至少有一点正文
    assert len(md.strip()) > 120


def test_order_db_has_three_samples() -> None:
    assert set(ORDER_DB) >= {"ORD-1001", "ORD-1002", "ORD-1003"}
