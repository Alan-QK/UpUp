"""Mock LLM：按序吐出预设 assistant 消息，便于离线单测。

本文件在练习中已给齐，今日勿改。
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MockLLM:
    """按顺序吐出预设 assistant 消息；记录每次入参 messages 的深拷贝。"""

    _responses: list[dict[str, Any]] = field(default_factory=list)
    calls: list[list[dict[str, Any]]] = field(default_factory=list)

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self._responses = [copy.deepcopy(item) for item in responses]
        self.calls = []

    def __call__(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        self.calls.append(copy.deepcopy(messages))
        if not self._responses:
            raise RuntimeError("no more scripted responses")
        return copy.deepcopy(self._responses.pop(0))


def assistant_text(content: str) -> dict[str, Any]:
    return {"role": "assistant", "content": content}


def assistant_tool_call(
    tool_name: str,
    arguments: dict[str, Any],
    *,
    call_id: str = "call_1",
    thought: str = "",
) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": thought,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": json.dumps(arguments, ensure_ascii=False),
                },
            }
        ],
    }


def parse_tool_arguments(raw: Any) -> dict[str, Any]:
    """把 tool_call.function.arguments（str 或 dict）解析成 dict。"""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return {}
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("tool arguments must be a JSON object")
        return data
    raise ValueError("tool arguments must be str or dict")
