"""Day 11 参考实现：OpenAI 兼容 Chat Completions（非流式）客户端。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Sequence

import httpx


class ChatClientError(Exception):
    """Chat 客户端相关错误的基类。"""


class ChatHttpError(ChatClientError):
    """HTTP 状态码不在 2xx。"""

    def __init__(self, status_code: int, body: str = "") -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {body[:200]}")


class ChatResponseError(ChatClientError):
    """响应无法按约定协议解析（非法 JSON / 缺字段等）。"""


@dataclass(frozen=True)
class ChatMessage:
    """一条对话消息。"""

    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class ChatCompletionResult:
    """一次非流式补全的解析结果。"""

    content: str
    model: str
    finish_reason: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


def _as_int(value: Any) -> int | None:
    """把 JSON 数字安全转成 int；无法转换则返回 None。"""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


class ChatClient:
    """面向 OpenAI 兼容 Chat Completions 的薄封装（仅非流式）。"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        model: str,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._model = model
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ChatClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float | None = None,
    ) -> ChatCompletionResult:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [m.to_dict() for m in messages],
            "stream": False,
        }
        if temperature is not None:
            payload["temperature"] = temperature

        resp = self._client.post("/chat/completions", json=payload)
        if resp.status_code < 200 or resp.status_code > 299:
            raise ChatHttpError(resp.status_code, resp.text)

        try:
            data = resp.json()
        except json.JSONDecodeError as exc:
            raise ChatResponseError("invalid json") from exc

        if not isinstance(data, dict):
            raise ChatResponseError("response is not a JSON object")

        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ChatResponseError("missing choices")

        first = choices[0]
        if not isinstance(first, dict):
            raise ChatResponseError("invalid choice")

        message = first.get("message")
        if not isinstance(message, dict):
            raise ChatResponseError("missing message")

        content = message.get("content")
        if not isinstance(content, str):
            raise ChatResponseError("missing content")

        finish_reason = first.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None

        model = data.get("model")
        if not isinstance(model, str) or not model:
            model = self._model

        usage = data.get("usage")
        prompt_tokens = completion_tokens = total_tokens = None
        if isinstance(usage, dict):
            prompt_tokens = _as_int(usage.get("prompt_tokens"))
            completion_tokens = _as_int(usage.get("completion_tokens"))
            total_tokens = _as_int(usage.get("total_tokens"))

        return ChatCompletionResult(
            content=content,
            model=model,
            finish_reason=finish_reason,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
