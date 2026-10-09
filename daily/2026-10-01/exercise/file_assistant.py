"""Day 50 练习：只读文件助手（权限边界 / 沙箱）。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库。
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

ChatFn = Callable[[list[dict[str, Any]]], dict[str, Any]]
PrintFn = Callable[[str], None]

ERROR_PREFIX = "ERROR:"

TOOL_LIST_DIR = "list_directory"
TOOL_READ_FILE = "read_file"
FILE_TOOL_NAMES: tuple[str, ...] = (TOOL_LIST_DIR, TOOL_READ_FILE)

STOP_FINAL = "final_answer"
STOP_MAX_STEPS = "max_steps"
VALID_STOP_REASONS = (STOP_FINAL, STOP_MAX_STEPS)


@dataclass(frozen=True)
class SandboxPolicy:
    """只读沙箱策略：所有路径必须落在 root 之下。"""

    root: Path
    max_read_bytes: int = 4096
    max_list_entries: int = 50
    max_steps: int = 6


@dataclass(frozen=True)
class AssistantResult:
    """只读文件助手一次运行结果。"""

    goal: str
    messages: list[dict[str, Any]]
    final_content: str
    stopped_reason: str
    tool_names_used: tuple[str, ...]
    steps: int


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


def validate_sandbox_policy(policy: SandboxPolicy) -> SandboxPolicy:
    """校验并规范化 SandboxPolicy。

    规则：
    - policy 必须是 SandboxPolicy，否则 TypeError
    - root 解析为绝对路径后必须存在且为目录，否则 ValueError
    - max_read_bytes / max_list_entries / max_steps 必须是 int 且 >= 1
    - 拒绝 bool（bool 是 int 子类）→ TypeError
    - 返回新的 SandboxPolicy（root 已 resolve）
    """
    # TODO: 实现
    raise NotImplementedError


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白压成单个空格。"""
    # TODO: 实现
    raise NotImplementedError


def resolve_sandbox_path(root: Path, user_path: str) -> Path:
    """把用户给出的路径解析到 root 之下。

    规则：
    - user_path 必须是非空 str（去空白后非空），否则 TypeError / ValueError
    - 禁止空字节 \\x00 → ValueError
    - 绝对路径：resolve 后必须位于 root 之下（含 root 自身）
    - 相对路径：以 root / user_path 解析，结果必须位于 root 之下
    - 用 Path.resolve() 消除 .. 与符号链接后再做前缀检查
    - 越界 → PermissionError，消息含 "escapes sandbox"
    """
    # TODO: 实现
    raise NotImplementedError


def list_directory(policy: SandboxPolicy, user_path: str = ".") -> dict[str, Any]:
    """列出沙箱内某目录的条目（只读）。

    返回：
    {
      "path": "<相对 root 的 posix 路径，root 自身为 '.'>",
      "entries": [{"name": str, "type": "file"|"dir"|"other"}, ...]
    }

    - 按 name 排序
    - 最多 max_list_entries 条；若被截断，加 "truncated": True
    - 目标不存在 → FileNotFoundError
    - 目标不是目录 → ValueError("not a directory")
    - 路径越界 → PermissionError（由 resolve_sandbox_path 抛出）
    """
    # TODO: 实现
    raise NotImplementedError


def read_text_file(policy: SandboxPolicy, user_path: str) -> dict[str, Any]:
    """读取沙箱内文本文件（只读，有字节上限）。

    返回：
    {
      "path": "<相对 root 的 posix 路径>",
      "content": str,
      "truncated": bool,
      "bytes_read": int
    }

    - 目标不存在 → FileNotFoundError
    - 目标不是文件 → ValueError("not a file")
    - 以字节截断到 max_read_bytes，再用 UTF-8 decode(errors='replace')
    """
    # TODO: 实现
    raise NotImplementedError


def build_list_directory_tool() -> dict[str, Any]:
    """返回 list_directory 的 OpenAI 风格 tool schema（已实现，可直接用）。"""
    return {
        "type": "function",
        "function": {
            "name": TOOL_LIST_DIR,
            "description": (
                "列出沙箱工作区内某个目录的文件与子目录（只读）。"
                "path 相对工作区根目录，默认 '.'。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "相对工作区的目录路径，如 '.'、'docs'",
                    },
                },
                "required": [],
            },
        },
    }


def build_read_file_tool() -> dict[str, Any]:
    """返回 read_file 的 OpenAI 风格 tool schema（已实现，可直接用）。"""
    return {
        "type": "function",
        "function": {
            "name": TOOL_READ_FILE,
            "description": (
                "读取沙箱工作区内某个文本文件的内容（只读，有大小上限）。"
                "不要尝试写入、删除或执行文件。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "相对工作区的文件路径，如 'README.md'、'docs/notes.md'",
                    },
                },
                "required": ["path"],
            },
        },
    }


def file_toolkit() -> list[dict[str, Any]]:
    """返回只读文件工具 schema 列表（已实现）。"""
    return [build_list_directory_tool(), build_read_file_tool()]


def default_system_prompt() -> str:
    """返回 system 提示（已实现）。"""
    names = "、".join(FILE_TOOL_NAMES)
    return (
        "你是一个只读文件助手。"
        f"可用工具：{names}。"
        "你只能列举目录与读取文件，不能写入、删除、移动或执行。"
        "所有路径都必须落在工作区沙箱内；越界请求会被拒绝。"
        "先 list_directory 摸清结构，再 read_file 读需要的文件，最后给出答案。"
    )


def parse_arguments(raw: Any) -> dict[str, Any]:
    """把 tool call 的 arguments 解析成 dict。

    规则：
    - None / 空白 str → {}
    - dict → 浅拷贝
    - JSON str 且为 object → dict
    - 非法 JSON → ValueError("arguments must be valid JSON")
    - JSON 非 object → ValueError("arguments JSON must be an object")
    - 其它类型 → ValueError("arguments must be str or dict")
    """
    # TODO: 实现
    raise NotImplementedError


def has_tool_calls(message: Any) -> bool:
    """message 是否为带非空 tool_calls 列表的 dict。"""
    # TODO: 实现
    raise NotImplementedError


def assistant_thought(message: dict[str, Any]) -> str:
    """取出 assistant content 并 normalize_text；content 为 None → ""。"""
    # TODO: 实现
    raise NotImplementedError


def execute_file_tools(
    assistant_message: dict[str, Any],
    policy: SandboxPolicy,
) -> list[dict[str, Any]]:
    """执行 assistant 消息中的只读文件工具调用，返回 tool 消息列表。

    规则：
    - 先 validate_sandbox_policy
    - assistant_message 非 dict → TypeError
    - 遍历 tool_calls：
      - list_directory：path 缺省为 "."
      - read_file：缺少 path → ValueError("missing required argument: path")
      - 未知工具 → ValueError("Unknown tool: ...")
      - 成功 → content 为 JSON 字符串（ensure_ascii=False）
      - 任意异常 → content = "ERROR: <ExcName>: <message>"
    - 每条返回 {"role":"tool","tool_call_id":...,"content":...}
    """
    # TODO: 实现
    raise NotImplementedError


def collect_tool_names(assistant_message: dict[str, Any]) -> list[str]:
    """按顺序收集 tool_calls 里的函数名（已实现，可直接用）。"""
    names: list[str] = []
    for call in assistant_message.get("tool_calls") or []:
        if not isinstance(call, dict):
            continue
        fn = call.get("function") or {}
        name = str(fn.get("name") or "")
        if name:
            names.append(name)
    return names


def run_readonly_assistant(
    goal: str,
    chat: ChatFn,
    policy: SandboxPolicy,
    *,
    system_prompt: str | None = None,
) -> AssistantResult:
    """只读文件助手主循环。

    规则：
    1. validate policy；goal 必须非空 str
    2. messages = [system, user(goal)]
    3. 最多 max_steps 轮：
       - assistant = chat(messages)；追加
       - 无 tool_calls → final_answer，final_content = content
       - 有 tool_calls → execute_file_tools 回填，记录工具名
    4. 步数耗尽仍无 final → stopped_reason=max_steps
    5. 返回 AssistantResult
    """
    # TODO: 实现
    raise NotImplementedError
