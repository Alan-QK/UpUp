"""Day 13 参考实现：OpenAI 兼容 Chat Completions（流式）客户端。"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Any, Sequence, TextIO

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
    """流式响应无法按约定协议解析。"""


@dataclass(frozen=True)
class ChatMessage:
    """一条对话消息。"""

    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


def parse_sse_data_line(line: str) -> str | None:
    """从一行 SSE 文本中提取 data payload。"""
    text = line.rstrip("\r")
    if not text.startswith("data:"):
        return None
    payload = text[len("data:") :]
    if payload.startswith(" "):
        payload = payload[1:]
    return payload


def extract_delta_text(payload: dict[str, Any]) -> str | None:
    """从流式 chunk JSON 中取出增量文本。"""
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0]
    if not isinstance(first, dict):
        return None
    delta = first.get("delta")
    if not isinstance(delta, dict):
        return None
    content = delta.get("content")
    if isinstance(content, str):
        return content
    return None


def print_stream(
    chunks: Iterable[str],
    *,
    file: TextIO | None = None,
) -> str:
    """把增量文本打印到终端（或指定 file），并返回拼接后的完整字符串。"""
    out = sys.stdout if file is None else file
    parts: list[str] = []
    for chunk in chunks:
        print(chunk, end="", flush=True, file=out)
        parts.append(chunk)
    print(file=out)
    return "".join(parts)


class StreamingChatClient:
    """面向 OpenAI 兼容 Chat Completions 的流式薄封装。"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        model: str,
        timeout: float = 60.0,
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

    def __enter__(self) -> StreamingChatClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def iter_content(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float | None = None,
    ) -> Iterator[str]:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [m.to_dict() for m in messages],
            "stream": True,
        }
        if temperature is not None:
            payload["temperature"] = temperature

        with self._client.stream(
            "POST", "/chat/completions", json=payload
        ) as resp:
            if resp.status_code < 200 or resp.status_code > 299:
                body = resp.read().decode("utf-8", errors="replace")
                raise ChatHttpError(resp.status_code, body)

            for line in resp.iter_lines():
                data = parse_sse_data_line(line)
                if data is None:
                    continue
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError as exc:
                    raise ChatResponseError("invalid json in sse data") from exc
                if not isinstance(obj, dict):
                    raise ChatResponseError("sse data is not a JSON object")
                text = extract_delta_text(obj)
                if text is not None:
                    yield text
