"""Day 49 练习：轨迹日志 Trace（每步 action/observation 可回放）。

请完成 TODO，使 tests/ 全部通过。
tools.py 已给齐，可直接 import。
全程只用标准库。
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from tools import execute_assistant_tools, loop_toolkit

ChatFn = Callable[[list[dict[str, Any]]], dict[str, Any]]
ExecuteFn = Callable[[dict[str, Any]], list[dict[str, Any]]]
PrintFn = Callable[[str], None]

ERROR_PREFIX = "ERROR:"

STOP_FINAL = "final_answer"
STOP_MAX_STEPS = "max_steps"
VALID_STOP_REASONS = (STOP_FINAL, STOP_MAX_STEPS)


@dataclass(frozen=True)
class TracePolicy:
    """轨迹记录策略。"""

    max_steps: int = 6
    live_print: bool = True


@dataclass(frozen=True)
class ActionRecord:
    """一次工具调用的结构化记录。"""

    call_id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ObservationRecord:
    """一次工具观察的结构化记录。"""

    call_id: str
    content: str
    is_error: bool


@dataclass(frozen=True)
class TraceStep:
    """Loop 中的一步轨迹。"""

    index: int
    kind: str  # "action" | "final"
    thought: str
    actions: tuple[ActionRecord, ...]
    observations: tuple[ObservationRecord, ...]


@dataclass(frozen=True)
class TraceLog:
    """完整可回放轨迹。"""

    goal: str
    steps: tuple[TraceStep, ...]
    stopped_reason: str
    final_content: str
    max_steps: int


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


def default_system_prompt() -> str:
    """返回 system 提示（已实现，可直接用）。"""
    names = "、".join(item["function"]["name"] for item in loop_toolkit())
    return (
        "你是带轨迹日志的 ReAct 助手。"
        f"可用工具：{names}。"
        "每一步都会被记录 Thought / Action / Observation。"
        "信息足够后直接给出最终回答。"
    )


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白压成单个空格。"""
    # TODO: 实现
    raise NotImplementedError


def has_tool_calls(assistant_message: dict[str, Any]) -> bool:
    """是否包含至少一条 tool_call。

    规则：
    - 非 dict → False
    - tool_calls 为非空 list → True
    - 否则 False
    """
    # TODO: 实现
    raise NotImplementedError


def assistant_thought(assistant_message: dict[str, Any]) -> str:
    """抽取 Thought（assistant.content）。

    规则：
    - 非 dict → ""
    - content 为 None → ""
    - 否则 normalize_text(str(content))
    """
    # TODO: 实现
    raise NotImplementedError


def parse_arguments(raw: Any) -> dict[str, Any]:
    """解析 tool_call.function.arguments。

    规则：
    - dict → 深拷贝后返回
    - None / "" / 只含空白的 str → {}
    - str → json.loads；失败则 ValueError("arguments must be valid JSON")
      解析结果必须是 dict，否则 ValueError("arguments JSON must be an object")
    - 其他类型 → ValueError("arguments must be str or dict")
    """
    # TODO: 实现
    raise NotImplementedError


def extract_actions(assistant_message: dict[str, Any]) -> tuple[ActionRecord, ...]:
    """从 assistant.tool_calls 提取 ActionRecord 元组。

    规则：
    - 非 dict 或 tool_calls 非 list → ()
    - 跳过非 dict 的 call
    - call_id = str(id).strip()；空则用 "unknown"
    - name：function 非 dict 或 name 空 → "unknown"
    - arguments：调用 parse_arguments；若抛 ValueError，用 {"_raw": str(原值), "_error": str(exc)}
    """
    # TODO: 实现
    raise NotImplementedError


def extract_observations(
    tool_messages: list[dict[str, Any]],
) -> tuple[ObservationRecord, ...]:
    """从 role=tool 消息列表提取 ObservationRecord。

    规则：
    - tool_messages 非 list → ()
    - 跳过非 dict
    - call_id = str(tool_call_id).strip()；空则 "unknown"
    - content：None → ""；否则 str(content)
    - is_error：content.lstrip() 以 ERROR_PREFIX 开头
    """
    # TODO: 实现
    raise NotImplementedError


def format_action_line(action: ActionRecord) -> str:
    """格式化单条 Action 行。

    形如：Action: lookup(key=alpha)
    - arguments 按 key 排序，写成 k=v（v 用 json.dumps ensure_ascii=False, separators 紧凑）
    - 无参数：Action: name()
    """
    # TODO: 实现
    raise NotImplementedError


def format_observation_line(observation: ObservationRecord) -> str:
    """格式化单条 Observation 行。

    - is_error=True → Observation ERROR: <content 去掉前导空白后原样>
    - 否则 → Observation: <content>
    """
    # TODO: 实现
    raise NotImplementedError


def format_step_block(step: TraceStep) -> str:
    """格式化一步的多行文本块（末尾无多余空行）。

    形如：
    Step 1 · action
      Thought: ...
      Action: lookup(key=alpha)
      Observation: {...}

    规则：
    - 首行：Step {index} · {kind}
    - 第二行：两个空格 + Thought: {thought or '(empty)'}
    - kind == "final"：到此结束（无 Action/Observation）
    - kind == "action"：
        - 每个 action 一行，前缀两个空格 + format_action_line
        - 若无 action：两个空格 + Action: (none)
        - 每个 observation 一行，前缀两个空格 + format_observation_line
        - 若无 observation：两个空格 + Observation: (none)
    """
    # TODO: 实现
    raise NotImplementedError


def render_trace_text(trace: TraceLog) -> str:
    """渲染完整可回放文本。

    要求包含：
    - 标题行：# Trace · {goal}
    - 空行
    - - max_steps={n}
    - 空行
    - 每步 format_step_block，步与步之间一空行
    - 结尾空行后：**Stopped:** ... / **Final:** ...
    """
    # TODO: 实现
    raise NotImplementedError


def action_to_dict(action: ActionRecord) -> dict[str, Any]:
    """ActionRecord → 可 JSON 序列化的 dict。"""
    # TODO: 实现（keys: call_id, name, arguments）
    raise NotImplementedError


def observation_to_dict(observation: ObservationRecord) -> dict[str, Any]:
    """ObservationRecord → dict。"""
    # TODO: 实现（keys: call_id, content, is_error）
    raise NotImplementedError


def step_to_dict(step: TraceStep) -> dict[str, Any]:
    """TraceStep → dict（含 type='step'）。"""
    # TODO: 实现
    # {
    #   "type": "step",
    #   "index": ...,
    #   "kind": ...,
    #   "thought": ...,
    #   "actions": [action_to_dict(...), ...],
    #   "observations": [observation_to_dict(...), ...],
    # }
    raise NotImplementedError


def step_from_dict(data: dict[str, Any]) -> TraceStep:
    """dict → TraceStep。

    规则：
    - data 必须是 dict，否则 TypeError("step data must be dict")
    - type 若存在且不是 "step" → ValueError("expected type=step")
    - actions / observations 缺省当 []
    """
    # TODO: 实现
    raise NotImplementedError


def validate_trace_policy(policy: TracePolicy) -> TracePolicy:
    """校验 TracePolicy。

    规则：
    - 必须是 TracePolicy，否则 TypeError("policy must be TracePolicy")
    - max_steps：必须是 int（bool 不算），否则 ValueError("max_steps must be int")
      且 >= 1，否则 ValueError("max_steps must be >= 1")
    - live_print：必须是 bool（只要 isinstance(..., bool)），否则
      ValueError("live_print must be bool")
    - 返回原 policy
    """
    # TODO: 实现
    raise NotImplementedError


def dump_trace_jsonl(path: str | Path, trace: TraceLog) -> None:
    """把 TraceLog 写成 JSONL 文件。

    行序：
    1. {"type":"meta","goal":...,"max_steps":...}
    2. 每个 step：step_to_dict(...)
    3. {"type":"end","stopped_reason":...,"final_content":...}

    使用 utf-8，ensure_ascii=False；每行一个 JSON + 换行。
    """
    # TODO: 实现
    raise NotImplementedError


def load_trace_jsonl(path: str | Path) -> TraceLog:
    """从 JSONL 加载 TraceLog。

    规则：
    - 必须先出现 type=meta，否则 ValueError("missing meta line")
    - 收集所有 type=step
    - 必须有 type=end，否则 ValueError("missing end line")
    - 忽略空行
    - 未知 type → ValueError("unknown jsonl type: ...")
    """
    # TODO: 实现
    raise NotImplementedError


def run_traced_loop(
    goal: str,
    chat: ChatFn,
    *,
    policy: TracePolicy | None = None,
    execute: ExecuteFn | None = None,
    system_prompt: str | None = None,
    printer: PrintFn | None = None,
) -> TraceLog:
    """带轨迹记录的 Agent Loop。

    流程：
    1. policy 默认 TracePolicy()；先 validate_trace_policy
    2. goal 经 normalize_text 后不得为空，否则 ValueError("goal must be non-empty")
    3. execute 默认 execute_assistant_tools；system 默认 default_system_prompt()
    4. printer 默认 print；仅当 policy.live_print 为 True 时，每步完成后
       printer(format_step_block(step))
    5. messages = [system, user(goal)]
    6. for index in 1..policy.max_steps:
         - assistant = chat(messages)；必须是 dict，否则 ValueError("chat must return dict")
         - 深拷贝 append；thought = assistant_thought(...)
         - 若无 tool_calls：
             step = TraceStep(index, "final", thought, (), ())
             追加；live print；返回 TraceLog(stopped_reason=final_answer, final_content=thought)
         - tool_msgs = execute(...)；必须是 list，否则 ValueError("execute must return list")
           深拷贝 append 每条
         - actions = extract_actions(...)；observations = extract_observations(...)
         - step = TraceStep(index, "action", thought, actions, observations)
         - 追加；live print
    7. 循环自然结束：
       TraceLog(..., stopped_reason=max_steps, final_content="(stopped: max_steps)")

    注意：
    - TraceLog.steps 为 tuple
    - TraceLog.max_steps 取自校验后的 policy.max_steps
    """
    # TODO: 实现
    raise NotImplementedError
