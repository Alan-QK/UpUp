"""Day 50 参考实现：只读文件助手（权限边界 / 沙箱）。"""

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
    - policy 必须是 SandboxPolicy
    - root 解析为绝对路径后必须存在且为目录
    - max_read_bytes / max_list_entries / max_steps 必须是 int 且 >= 1
    - 拒绝 bool（bool 是 int 子类）
    """
    if not isinstance(policy, SandboxPolicy):
        raise TypeError("policy must be SandboxPolicy")

    root = Path(policy.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("root must be an existing directory")

    for name, value in (
        ("max_read_bytes", policy.max_read_bytes),
        ("max_list_entries", policy.max_list_entries),
        ("max_steps", policy.max_steps),
    ):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be int")
        if value < 1:
            raise ValueError(f"{name} must be >= 1")

    return SandboxPolicy(
        root=root,
        max_read_bytes=policy.max_read_bytes,
        max_list_entries=policy.max_list_entries,
        max_steps=policy.max_steps,
    )


def normalize_text(text: str) -> str:
    """去掉首尾空白，并把内部连续空白压成单个空格。"""
    return " ".join(text.split())


def resolve_sandbox_path(root: Path, user_path: str) -> Path:
    """把用户给出的路径解析到 root 之下。

    规则：
    - user_path 必须是非空 str（去空白后非空）
    - 禁止空字节 \\x00
    - 若为绝对路径：resolve 后必须位于 root 之下（含 root 自身）
    - 若为相对路径：以 root / user_path 解析，结果必须位于 root 之下
    - 用 Path.resolve() 消除 .. 与符号链接后再做前缀检查
    - 越界 → PermissionError，消息含 "escapes sandbox"
    """
    if not isinstance(user_path, str):
        raise TypeError("user_path must be str")
    cleaned = user_path.strip()
    if not cleaned:
        raise ValueError("user_path must be non-empty")
    if "\x00" in cleaned:
        raise ValueError("user_path must not contain NUL")

    root_resolved = root.resolve()
    candidate = Path(cleaned)
    if candidate.is_absolute():
        target = candidate.resolve()
    else:
        target = (root_resolved / candidate).resolve()

    try:
        target.relative_to(root_resolved)
    except ValueError as exc:
        raise PermissionError("path escapes sandbox") from exc
    return target


def list_directory(policy: SandboxPolicy, user_path: str = ".") -> dict[str, Any]:
    """列出沙箱内某目录的条目（只读）。

    返回：
    {
      "path": "<相对 root 的 posix 路径，root 自身为 '.'>",
      "entries": [{"name": str, "type": "file"|"dir"|"other"}, ...]
    }

    - 按 name 排序
    - 最多 max_list_entries 条（截断时加 "truncated": True）
    - 目标不是目录 → ValueError
    - 路径越界 → PermissionError（由 resolve_sandbox_path 抛出）
    """
    policy = validate_sandbox_policy(policy)
    target = resolve_sandbox_path(policy.root, user_path)
    if not target.exists():
        raise FileNotFoundError(f"directory not found: {user_path}")
    if not target.is_dir():
        raise ValueError("not a directory")

    entries: list[dict[str, str]] = []
    for child in sorted(target.iterdir(), key=lambda p: p.name):
        if child.is_dir():
            kind = "dir"
        elif child.is_file():
            kind = "file"
        else:
            kind = "other"
        entries.append({"name": child.name, "type": kind})

    rel = _rel_display(policy.root, target)
    result: dict[str, Any] = {"path": rel, "entries": entries[: policy.max_list_entries]}
    if len(entries) > policy.max_list_entries:
        result["truncated"] = True
    return result


def read_text_file(policy: SandboxPolicy, user_path: str) -> dict[str, Any]:
    """读取沙箱内文本文件（只读，有字节上限）。

    返回：
    {
      "path": "<相对 root 的 posix 路径>",
      "content": str,
      "truncated": bool,
      "bytes_read": int
    }

    - 目标不是文件 → ValueError
    - 以字节截断到 max_read_bytes，再用 UTF-8 decode（errors='replace')
    """
    policy = validate_sandbox_policy(policy)
    target = resolve_sandbox_path(policy.root, user_path)
    if not target.exists():
        raise FileNotFoundError(f"file not found: {user_path}")
    if not target.is_file():
        raise ValueError("not a file")

    raw = target.read_bytes()
    truncated = len(raw) > policy.max_read_bytes
    chunk = raw[: policy.max_read_bytes]
    content = chunk.decode("utf-8", errors="replace")
    return {
        "path": _rel_display(policy.root, target),
        "content": content,
        "truncated": truncated,
        "bytes_read": len(chunk),
    }


def _rel_display(root: Path, target: Path) -> str:
    rel = target.resolve().relative_to(root.resolve())
    text = rel.as_posix()
    return "." if text == "." else text


def build_list_directory_tool() -> dict[str, Any]:
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
    """返回只读文件工具 schema 列表。"""
    return [build_list_directory_tool(), build_read_file_tool()]


def default_system_prompt() -> str:
    names = "、".join(FILE_TOOL_NAMES)
    return (
        "你是一个只读文件助手。"
        f"可用工具：{names}。"
        "你只能列举目录与读取文件，不能写入、删除、移动或执行。"
        "所有路径都必须落在工作区沙箱内；越界请求会被拒绝。"
        "先 list_directory 摸清结构，再 read_file 读需要的文件，最后给出答案。"
    )


def parse_arguments(raw: Any) -> dict[str, Any]:
    """把 tool call 的 arguments 解析成 dict。"""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    if not isinstance(raw, str):
        raise ValueError("arguments must be str or dict")
    text = raw.strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("arguments must be valid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("arguments JSON must be an object")
    return data


def has_tool_calls(message: Any) -> bool:
    if not isinstance(message, dict):
        return False
    calls = message.get("tool_calls")
    return isinstance(calls, list) and len(calls) > 0


def assistant_thought(message: dict[str, Any]) -> str:
    content = message.get("content")
    if content is None:
        return ""
    return normalize_text(str(content))


def _error_content(exc: BaseException) -> str:
    return f"{ERROR_PREFIX} {type(exc).__name__}: {exc}"


def execute_file_tools(
    assistant_message: dict[str, Any],
    policy: SandboxPolicy,
) -> list[dict[str, Any]]:
    """执行 assistant 消息中的只读文件工具调用，返回 tool 消息列表。

    - 未知工具名 → ERROR: Unknown tool
    - 参数 / 权限 / IO 失败 → ERROR: ...
    - 成功 → JSON 字符串（ensure_ascii=False）
    """
    policy = validate_sandbox_policy(policy)
    if not isinstance(assistant_message, dict):
        raise TypeError("assistant_message must be dict")

    calls = assistant_message.get("tool_calls") or []
    results: list[dict[str, Any]] = []
    for call in calls:
        if not isinstance(call, dict):
            continue
        call_id = str(call.get("id") or "")
        fn = call.get("function") or {}
        name = str(fn.get("name") or "")
        try:
            args = parse_arguments(fn.get("arguments"))
            if name == TOOL_LIST_DIR:
                path = str(args.get("path", ".") or ".")
                payload = list_directory(policy, path)
            elif name == TOOL_READ_FILE:
                if "path" not in args:
                    raise ValueError("missing required argument: path")
                payload = read_text_file(policy, str(args["path"]))
            else:
                raise ValueError(f"Unknown tool: {name}")
            content = json.dumps(payload, ensure_ascii=False)
        except Exception as exc:  # noqa: BLE001 - 工具层统一 ERROR 回填
            content = _error_content(exc)
        results.append(
            {
                "role": "tool",
                "tool_call_id": call_id,
                "content": content,
            }
        )
    return results


def collect_tool_names(assistant_message: dict[str, Any]) -> list[str]:
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

    1. system + user(goal)
    2. 最多 max_steps 轮：chat → 若无 tool_calls 则 final；否则执行工具并回填
    3. 步数耗尽 → stopped_reason=max_steps
    """
    policy = validate_sandbox_policy(policy)
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("goal must be non-empty str")

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt or default_system_prompt()},
        {"role": "user", "content": goal.strip()},
    ]
    used: list[str] = []
    steps = 0
    final_content = ""
    stopped = STOP_MAX_STEPS

    for _ in range(policy.max_steps):
        steps += 1
        assistant = chat(messages)
        if not isinstance(assistant, dict) or assistant.get("role") != "assistant":
            raise TypeError("chat must return assistant message dict")
        messages.append(assistant)

        if not has_tool_calls(assistant):
            final_content = str(assistant.get("content") or "")
            stopped = STOP_FINAL
            break

        used.extend(collect_tool_names(assistant))
        tool_msgs = execute_file_tools(assistant, policy)
        messages.extend(tool_msgs)
    # 步数耗尽且未 final 时：stopped 保持 max_steps，final_content 保持 ""

    return AssistantResult(
        goal=goal.strip(),
        messages=messages,
        final_content=final_content,
        stopped_reason=stopped,
        tool_names_used=tuple(used),
        steps=steps,
    )
