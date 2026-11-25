"""Day 11 练习：OpenAI 兼容 Chat Completions（非流式）客户端。

请完成 TODO，使 tests/ 全部通过。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import httpx


class ChatClientError(Exception):
    """Chat 客户端相关错误的基类。"""


class ChatHttpError(ChatClientError):
    """HTTP 状态码不在 2xx。

    Attributes:
        status_code: 响应状态码
        body: 响应文本（便于调试；可能为空）
    """

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


class ChatClient:
    """面向 OpenAI 兼容 Chat Completions 的薄封装（仅非流式）。

    约定：
    - base_url 形如 https://api.openai.com/v1（不要带尾斜杠也行，httpx 会处理）
    - 请求 path：/chat/completions
    - Header：Authorization: Bearer <api_key>
    - 支持 context manager；transport 可选，供 MockTransport 注入
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        model: str,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        # TODO: 保存 model；创建 httpx.Client
        # 提示：
        #   headers = {
        #       "Authorization": f"Bearer {api_key}",
        #       "Content-Type": "application/json",
        #   }
        #   httpx.Client(base_url=..., timeout=..., headers=..., transport=...)
        raise NotImplementedError

    def close(self) -> None:
        """关闭底层 Client。"""
        # TODO: 实现这里
        raise NotImplementedError

    def __enter__(self) -> ChatClient:
        # TODO: 返回 self
        raise NotImplementedError

    def __exit__(self, *args: object) -> None:
        # TODO: 调用 close()
        raise NotImplementedError

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float | None = None,
    ) -> ChatCompletionResult:
        """发起非流式 Chat Completions，返回解析后的结果。

        请求 JSON 必须包含：
        - model: 构造时传入的模型名
        - messages: [m.to_dict() for m in messages]
        - stream: False

        若 temperature 非 None，则一并写入请求体。

        解析规则：
        - status 不在 200–299 → ChatHttpError(status_code, response.text)
        - 响应不是合法 JSON object → ChatResponseError
        - 缺少 choices[0].message.content（或 content 不是 str）→ ChatResponseError
        - model 字段：优先用响应里的 model；若缺失则回退为构造时的 model
        - finish_reason：choices[0].get("finish_reason")，可为 None
        - usage 下 prompt_tokens / completion_tokens / total_tokens：有则填入，缺则 None
        """
        # TODO: 实现这里
        # 提示：resp = self._client.post("/chat/completions", json=payload)
        raise NotImplementedError


def _as_int(value: Any) -> int | None:
    """把 JSON 数字安全转成 int；无法转换则返回 None。"""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None
