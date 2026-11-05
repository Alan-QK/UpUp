"""Day 53 附带：教学迷你框架（沿用 Day52 完成版，今日主战场在 business_tools.py）。"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Callable

from tools_builtin import (
    builtin_tool_metas,
    format_tool_result,
    normalize_text,
)

ChatFn = Callable[[list[dict[str, Any]]], dict[str, Any]]

STOP_FINAL = "final_answer"
STOP_MAX_STEPS = "max_steps"
VALID_STOP_REASONS = (STOP_FINAL, STOP_MAX_STEPS)

ERROR_PREFIX = "ERROR:"

HANDWRITTEN_KEYS = (
    "run_agent_loop",
    "loop_toolkit_and_execute",
    "messages_list",
    "LoopResult",
    "max_steps",
    "ScriptedChat",
)


@dataclass(frozen=True)
class Tool:
    """框架里的「一个工具」：名字 + 描述 + JSON Schema + 可调用 handler。"""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]


@dataclass
class ToolRegistry:
    """工具注册表：白名单 + schema 列表 + 按名执行。"""

    _tools: dict[str, Tool] = field(default_factory=dict)

    def register(self, tool: Tool) -> None:
        if not isinstance(tool, Tool):
            raise TypeError("tool must be Tool")
        name = normalize_text(tool.name)
        if not name:
            raise ValueError("tool.name must be non-empty")
        self._tools[name] = Tool(
            name=name,
            description=tool.description,
            parameters=copy.deepcopy(tool.parameters),
            handler=tool.handler,
        )

    def get(self, name: str) -> Tool | None:
        if not isinstance(name, str):
            return None
        return self._tools.get(normalize_text(name))

    def names(self) -> tuple[str, ...]:
        return tuple(self._tools.keys())

    def openai_tools(self) -> list[dict[str, Any]]:
        return [to_openai_tool_schema(tool) for tool in self._tools.values()]

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        tool = self.get(name)
        if tool is None:
            return f"{ERROR_PREFIX} Unknown tool: {name}"
        try:
            if not isinstance(arguments, dict):
                raise TypeError("arguments must be dict")
            result = tool.handler(**arguments)
            return format_tool_result(result)
        except Exception as exc:  # noqa: BLE001 - 工具错误要回填观察
            return f"{ERROR_PREFIX} {type(exc).__name__}: {exc}"

    def execute_assistant_tools(
        self, assistant_message: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if not isinstance(assistant_message, dict):
            raise TypeError("assistant_message must be dict")
        raw_calls = assistant_message.get("tool_calls") or []
        if not isinstance(raw_calls, list):
            raise TypeError("tool_calls must be list")

        observations: list[dict[str, Any]] = []
        for call in raw_calls:
            if not isinstance(call, dict):
                continue
            call_id = str(call.get("id") or "")
            fn = call.get("function") or {}
            if not isinstance(fn, dict):
                content = f"{ERROR_PREFIX} TypeError: function must be dict"
            else:
                tool_name = str(fn.get("name") or "")
                try:
                    args = parse_tool_arguments(fn.get("arguments"))
                    content = self.execute(tool_name, args)
                except Exception as exc:  # noqa: BLE001
                    content = f"{ERROR_PREFIX} {type(exc).__name__}: {exc}"
            observations.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": content,
                }
            )
        return observations


@dataclass(frozen=True)
class FrameworkAgent:
    """框架风格的 Agent 配置（还不跑 Loop，只持有策略）。"""

    name: str
    registry: ToolRegistry
    system_prompt: str
    max_steps: int = 6


@dataclass
class AgentState:
    """一次运行中的可变状态（对照手写 messages 列表）。"""

    messages: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class AgentRunResult:
    """一次 Runner 运行结果（对照 Day46 LoopResult）。"""

    goal: str
    messages: list[dict[str, Any]]
    final_content: str
    stopped_reason: str
    steps: int
    tool_names_used: tuple[str, ...]


class ScriptedChat:
    """按顺序吐出预设 assistant 消息；记录每次入参 messages 的深拷贝。"""

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self._responses = [copy.deepcopy(item) for item in responses]
        self.calls: list[list[dict[str, Any]]] = []

    def __call__(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        self.calls.append(copy.deepcopy(messages))
        if not self._responses:
            raise RuntimeError("no more scripted responses")
        return copy.deepcopy(self._responses.pop(0))


class AgentRunner:
    """框架执行器：内部仍是 while Loop（对照 Day46 run_agent_loop）。"""

    def run(self, agent: FrameworkAgent, goal: str, chat: ChatFn) -> AgentRunResult:
        if not isinstance(agent, FrameworkAgent):
            raise TypeError("agent must be FrameworkAgent")
        max_steps = validate_max_steps(agent.max_steps)
        cleaned_goal = normalize_text(goal)
        if not cleaned_goal:
            raise ValueError("goal must be non-empty")

        state = AgentState(
            messages=[
                {"role": "system", "content": agent.system_prompt},
                {"role": "user", "content": cleaned_goal},
            ]
        )
        used: list[str] = []

        for step_index in range(1, max_steps + 1):
            assistant = chat(state.messages)
            if not isinstance(assistant, dict):
                raise ValueError("chat must return dict")

            assistant_copy = copy.deepcopy(assistant)
            state.messages.append(assistant_copy)
            thought = assistant_thought(assistant_copy)

            if not has_tool_calls(assistant_copy):
                return AgentRunResult(
                    goal=cleaned_goal,
                    messages=copy.deepcopy(state.messages),
                    final_content=thought,
                    stopped_reason=STOP_FINAL,
                    steps=step_index,
                    tool_names_used=tuple(used),
                )

            for call in assistant_copy.get("tool_calls") or []:
                if isinstance(call, dict):
                    fn = call.get("function") or {}
                    if isinstance(fn, dict) and fn.get("name"):
                        used.append(str(fn["name"]))

            tool_msgs = agent.registry.execute_assistant_tools(assistant_copy)
            if not isinstance(tool_msgs, list):
                raise ValueError("execute_assistant_tools must return list")
            for item in tool_msgs:
                state.messages.append(copy.deepcopy(item))

        return AgentRunResult(
            goal=cleaned_goal,
            messages=copy.deepcopy(state.messages),
            final_content="(stopped: max_steps)",
            stopped_reason=STOP_MAX_STEPS,
            steps=max_steps,
            tool_names_used=tuple(used),
        )


def to_openai_tool_schema(tool: Tool) -> dict[str, Any]:
    if not isinstance(tool, Tool):
        raise TypeError("tool must be Tool")
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": copy.deepcopy(tool.parameters),
        },
    }


def tool_from_meta(meta: dict[str, Any]) -> Tool:
    if not isinstance(meta, dict):
        raise TypeError("meta must be dict")
    name = meta.get("name")
    description = meta.get("description")
    parameters = meta.get("parameters")
    handler = meta.get("handler")
    if not isinstance(name, str) or not normalize_text(name):
        raise ValueError("meta.name must be non-empty str")
    if not isinstance(description, str):
        raise TypeError("meta.description must be str")
    if not isinstance(parameters, dict):
        raise TypeError("meta.parameters must be dict")
    if not callable(handler):
        raise TypeError("meta.handler must be callable")
    return Tool(
        name=normalize_text(name),
        description=description,
        parameters=copy.deepcopy(parameters),
        handler=handler,
    )


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for meta in builtin_tool_metas():
        registry.register(tool_from_meta(meta))
    return registry


def default_system_prompt(registry: ToolRegistry) -> str:
    names = "、".join(registry.names())
    return (
        "你是框架风格助手，内部仍遵循 Thought → Action → Observation。"
        f"可用工具：{names}。"
        "需要事实时先 lookup；需要精确运算时 calculate。"
        "信息足够后直接给出最终回答，不要再调用工具。"
    )


def build_default_agent(
    *,
    name: str = "week10-twin",
    max_steps: int = 6,
) -> FrameworkAgent:
    registry = build_default_registry()
    return FrameworkAgent(
        name=name,
        registry=registry,
        system_prompt=default_system_prompt(registry),
        max_steps=validate_max_steps(max_steps),
    )


def has_tool_calls(assistant_message: dict[str, Any]) -> bool:
    if not isinstance(assistant_message, dict):
        return False
    raw = assistant_message.get("tool_calls")
    return isinstance(raw, list) and len(raw) > 0


def assistant_thought(assistant_message: dict[str, Any]) -> str:
    if not isinstance(assistant_message, dict):
        return ""
    content = assistant_message.get("content")
    if content is None:
        return ""
    return normalize_text(str(content))


def validate_max_steps(max_steps: int) -> int:
    if isinstance(max_steps, bool) or not isinstance(max_steps, int):
        raise ValueError("max_steps must be int")
    if max_steps < 1:
        raise ValueError("max_steps must be >= 1")
    return max_steps


def parse_tool_arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("arguments must be valid JSON object") from exc
        if not isinstance(parsed, dict):
            raise ValueError("arguments JSON must be object")
        return parsed
    raise ValueError("arguments must be dict or JSON object string")


def concept_mapping() -> dict[str, str]:
    return {
        "run_agent_loop": "AgentRunner.run（内部仍是 while Loop）",
        "loop_toolkit_and_execute": "ToolRegistry（openai_tools + execute）",
        "messages_list": "AgentState.messages",
        "LoopResult": "AgentRunResult",
        "max_steps": "FrameworkAgent.max_steps",
        "ScriptedChat": "ScriptedChat（同一 mock chat 适配器）",
    }


def render_mapping_markdown(mapping: dict[str, str] | None = None) -> str:
    data = mapping if mapping is not None else concept_mapping()
    if not isinstance(data, dict):
        raise TypeError("mapping must be dict")
    lines = [
        "# 手写 ↔ 框架 概念对照",
        "",
        "| 手写（Day46） | 迷你框架（Day52） |",
        "|---------------|------------------|",
    ]
    for key in HANDWRITTEN_KEYS:
        value = data.get(key, "")
        lines.append(f"| `{key}` | {value} |")
    lines.append("")
    lines.append("> 框架只是把样板代码收进了类；Loop 语义不变。")
    return "\n".join(lines)
