"""Day 52 测试：迷你框架重写手写 Agent（对照 Day46 同能力）。"""

from __future__ import annotations

import json

import pytest

from mini_framework import (
    ERROR_PREFIX,
    HANDWRITTEN_KEYS,
    STOP_FINAL,
    STOP_MAX_STEPS,
    AgentRunner,
    FrameworkAgent,
    ScriptedChat,
    Tool,
    ToolRegistry,
    assistant_thought,
    build_default_agent,
    build_default_registry,
    concept_mapping,
    has_tool_calls,
    parse_tool_arguments,
    render_mapping_markdown,
    to_openai_tool_schema,
    tool_from_meta,
    validate_max_steps,
)
from tools_builtin import LOOKUP_KB, builtin_tool_metas


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


def test_validate_max_steps() -> None:
    assert validate_max_steps(3) == 3
    with pytest.raises(ValueError):
        validate_max_steps(0)
    with pytest.raises(ValueError):
        validate_max_steps(True)  # type: ignore[arg-type]


def test_tool_from_meta_and_schema() -> None:
    meta = builtin_tool_metas()[0]
    tool = tool_from_meta(meta)
    assert tool.name == "lookup"
    schema = to_openai_tool_schema(tool)
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "lookup"
    assert "key" in schema["function"]["parameters"]["properties"]


def test_registry_register_execute_unknown() -> None:
    registry = build_default_registry()
    assert registry.names() == ("lookup", "calculate")
    assert registry.execute("lookup", {"key": "alpha"}) == LOOKUP_KB["alpha"]
    assert registry.execute("calculate", {"expression": "7*3"}) == "21"
    err = registry.execute("shell", {"cmd": "ls"})
    assert err.startswith(ERROR_PREFIX)
    assert "Unknown tool" in err


def test_registry_openai_tools_order() -> None:
    tools = build_default_registry().openai_tools()
    assert [t["function"]["name"] for t in tools] == ["lookup", "calculate"]


def test_execute_assistant_tools_happy_path() -> None:
    registry = build_default_registry()
    assistant = {
        "role": "assistant",
        "content": "查一下",
        "tool_calls": [_call("t1", "lookup", {"key": "beta"})],
    }
    obs = registry.execute_assistant_tools(assistant)
    assert len(obs) == 1
    assert obs[0]["role"] == "tool"
    assert obs[0]["tool_call_id"] == "t1"
    assert obs[0]["content"] == "3"


def test_execute_assistant_tools_bad_args_returns_error() -> None:
    registry = build_default_registry()
    assistant = {
        "role": "assistant",
        "content": "",
        "tool_calls": [_call("t1", "lookup", "{not-json")],
    }
    obs = registry.execute_assistant_tools(assistant)
    assert obs[0]["content"].startswith(ERROR_PREFIX)


def test_has_tool_calls_and_thought() -> None:
    assert has_tool_calls({"tool_calls": [_call("1", "lookup", {})]})
    assert not has_tool_calls({"role": "assistant", "content": "done"})
    assert not has_tool_calls({"tool_calls": []})
    assert assistant_thought({"content": "  hello   world "}) == "hello world"
    assert assistant_thought({"content": None}) == ""


def test_parse_tool_arguments() -> None:
    assert parse_tool_arguments({"a": 1}) == {"a": 1}
    assert parse_tool_arguments('{"a": 2}') == {"a": 2}
    with pytest.raises(ValueError):
        parse_tool_arguments("[1,2]")
    with pytest.raises(ValueError):
        parse_tool_arguments(123)


def test_runner_multi_step_final() -> None:
    agent = build_default_agent(max_steps=6)
    chat = ScriptedChat(
        [
            {
                "role": "assistant",
                "content": "lookup",
                "tool_calls": [_call("c1", "lookup", {"key": "alpha"})],
            },
            {
                "role": "assistant",
                "content": "calc",
                "tool_calls": [_call("c2", "calculate", {"expression": "7*3"})],
            },
            {"role": "assistant", "content": "结果是 21"},
        ]
    )
    result = AgentRunner().run(agent, "查 alpha 再乘以 3", chat)
    assert result.stopped_reason == STOP_FINAL
    assert result.steps == 3
    assert result.final_content == "结果是 21"
    assert result.tool_names_used == ("lookup", "calculate")
    # 第二轮入参应已包含第一轮 tool observation
    assert any(
        m.get("role") == "tool" and m.get("content") == "7"
        for m in chat.calls[1]
    )


def test_runner_max_steps() -> None:
    agent = build_default_agent(max_steps=2)
    chat = ScriptedChat(
        [
            {
                "role": "assistant",
                "content": "a",
                "tool_calls": [_call("c1", "lookup", {"key": "alpha"})],
            },
            {
                "role": "assistant",
                "content": "b",
                "tool_calls": [_call("c2", "lookup", {"key": "beta"})],
            },
        ]
    )
    result = AgentRunner().run(agent, "不停查", chat)
    assert result.stopped_reason == STOP_MAX_STEPS
    assert result.steps == 2
    assert result.final_content == "(stopped: max_steps)"


def test_runner_rejects_empty_goal() -> None:
    agent = build_default_agent()
    with pytest.raises(ValueError):
        AgentRunner().run(agent, "   ", ScriptedChat([]))


def test_build_default_agent_wires_registry() -> None:
    agent = build_default_agent(name="demo", max_steps=4)
    assert isinstance(agent, FrameworkAgent)
    assert agent.name == "demo"
    assert agent.max_steps == 4
    assert "lookup" in agent.system_prompt
    assert agent.registry.get("calculate") is not None


def test_register_rejects_bad_tool() -> None:
    registry = ToolRegistry()
    with pytest.raises(TypeError):
        registry.register({"name": "x"})  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        registry.register(
            Tool(name="  ", description="d", parameters={}, handler=lambda: None)
        )


def test_concept_mapping_and_markdown() -> None:
    mapping = concept_mapping()
    for key in HANDWRITTEN_KEYS:
        assert key in mapping
        assert isinstance(mapping[key], str)
        assert mapping[key].strip()

    assert "AgentRunner" in mapping["run_agent_loop"]
    assert "ToolRegistry" in mapping["loop_toolkit_and_execute"]
    assert "AgentState" in mapping["messages_list"]
    assert "AgentRunResult" in mapping["LoopResult"]
    assert "FrameworkAgent" in mapping["max_steps"]

    md = render_mapping_markdown(mapping)
    assert "手写" in md
    assert "run_agent_loop" in md
    assert "AgentRunner" in md
