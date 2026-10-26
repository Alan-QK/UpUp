"""Day 52 练习：教学迷你框架 —— 用框架 API 重写手写 Agent。

请完成 TODO，使 tests/ 全部通过。
tools_builtin.py 已给齐，可直接 import。
全程只用标准库——今天是「对照重写」，不是真装 LangChain。
"""

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

# 手写概念 → 迷你框架概念（练习需原样返回这些键）
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
        """注册工具；同名覆盖。"""
        # TODO: 校验 tool 类型与 name，写入 _tools
        raise NotImplementedError

    def get(self, name: str) -> Tool | None:
        """按名取工具；不存在返回 None。"""
        # TODO
        raise NotImplementedError

    def names(self) -> tuple[str, ...]:
        """按注册顺序返回工具名（dict 插入序）。"""
        # TODO
        raise NotImplementedError

    def openai_tools(self) -> list[dict[str, Any]]:
        """导出 OpenAI function-calling 风格的 tools 列表。"""
        # TODO: 对每个 Tool 调用 to_openai_tool_schema
        raise NotImplementedError

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        """执行命名工具；未知工具或异常 → 返回 ERROR: ... 字符串（不抛给 Loop）。"""
        # TODO
        raise NotImplementedError

    def execute_assistant_tools(self, assistant_message: dict[str, Any]) -> list[dict[str, Any]]:
        """解析 assistant.tool_calls，返回 role=tool 的 observation 消息列表。"""
        # TODO
        raise NotImplementedError


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
        """运行 Agent，直到 final_answer 或 max_steps。"""
        # TODO: 实现与 Day46 同语义的 Loop
        raise NotImplementedError


def to_openai_tool_schema(tool: Tool) -> dict[str, Any]:
    """把 Tool 转成 {"type":"function","function":{name,description,parameters}}。"""
    # TODO
    raise NotImplementedError


def tool_from_meta(meta: dict[str, Any]) -> Tool:
    """从 builtin meta dict 构造 Tool。

    meta 需含 name / description / parameters / handler。
    """
    # TODO
    raise NotImplementedError


def build_default_registry() -> ToolRegistry:
    """注册 lookup + calculate 两个内置工具。"""
    # TODO: builtin_tool_metas → tool_from_meta → register
    raise NotImplementedError


def default_system_prompt(registry: ToolRegistry) -> str:
    """根据已注册工具名生成 system 提示（已实现，可直接用）。"""
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
    """组装默认 Agent（registry + system + max_steps）。"""
    # TODO
    raise NotImplementedError


def has_tool_calls(assistant_message: dict[str, Any]) -> bool:
    """是否包含至少一条 tool_call。"""
    # TODO
    raise NotImplementedError


def assistant_thought(assistant_message: dict[str, Any]) -> str:
    """抽取 Thought 文本（assistant.content），做 normalize_text。"""
    # TODO
    raise NotImplementedError


def validate_max_steps(max_steps: int) -> int:
    """校验 max_steps：必须是 int 且 >= 1；拒绝 bool。"""
    # TODO
    raise NotImplementedError


def parse_tool_arguments(raw: Any) -> dict[str, Any]:
    """把 tool_call.function.arguments 解析为 dict。

    规则：
    - 已是 dict → 浅拷贝返回
    - str → json.loads，必须是 object
    - 其他 / 解析失败 → ValueError
    """
    # TODO
    raise NotImplementedError


def concept_mapping() -> dict[str, str]:
    """返回手写概念 → 迷你框架概念的对照字典。

    必须包含 HANDWRITTEN_KEYS 中的每一个键，值为非空 str。
    建议值（测试会检查关键子串）：
    - run_agent_loop → AgentRunner.run
    - loop_toolkit_and_execute → ToolRegistry
    - messages_list → AgentState.messages
    - LoopResult → AgentRunResult
    - max_steps → FrameworkAgent.max_steps
    - ScriptedChat → ScriptedChat（可注明同一 mock）
    """
    # TODO
    raise NotImplementedError


def render_mapping_markdown(mapping: dict[str, str] | None = None) -> str:
    """渲染手写 ↔ 框架对照表 Markdown。"""
    # TODO: 表头 + 每一行 | 手写 | 框架 |
    raise NotImplementedError
