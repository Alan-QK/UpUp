"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence, runtime_checkable

import httpx


class ProviderError(ValueError):
    """Provider 配置或调用不合法。"""


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


@dataclass(frozen=True)
class ProviderCall:
    """Fake 记录的一次 complete 调用（便于测试断言）。"""

    messages: tuple[ChatMessage, ...]
    temperature: float | None
    top_p: float | None


@runtime_checkable
class ChatProvider(Protocol):
    """聊天补全能力的最小协议（非流式）。"""

    @property
    def name(self) -> str: ...

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float | None = None,
        top_p: float | None = None,
    ) -> ChatCompletionResult: ...

    def close(self) -> None: ...


def last_user_content(messages: Sequence[ChatMessage]) -> str:
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    return ""


class FakeChatProvider:
    def __init__(
        self,
        *,
        model: str = "fake-model",
        default_reply: str = "（假模型默认回复）",
        replies: Mapping[str, str] | None = None,
    ) -> None:
        self._model = model
        self._default_reply = default_reply
        self._replies = dict(replies or {})
        self.calls: list[ProviderCall] = []

    @property
    def name(self) -> str:
        return "fake"

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float | None = None,
        top_p: float | None = None,
    ) -> ChatCompletionResult:
        if not messages:
            raise ProviderError("messages must not be empty")

        snapshot = tuple(messages)
        self.calls.append(
            ProviderCall(
                messages=snapshot,
                temperature=temperature,
                top_p=top_p,
            )
        )

        key = last_user_content(messages)
        content = self._replies.get(key, self._default_reply)
        prompt_tokens = sum(len(m.content) for m in messages)
        completion_tokens = len(content)
        return ChatCompletionResult(
            content=content,
            model=self._model,
            finish_reason="stop",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )

    def close(self) -> None:
        return None


def create_chat_provider(
    kind: str,
    *,
    model: str,
    api_key: str = "",
    base_url: str = "https://api.openai.com/v1",
    timeout: float = 30.0,
    transport: httpx.BaseTransport | None = None,
    default_reply: str = "（假模型默认回复）",
    replies: Mapping[str, str] | None = None,
) -> ChatProvider:
    normalized = kind.strip().lower()
    if not normalized:
        raise ProviderError("provider kind must not be empty")

    if normalized == "fake":
        return FakeChatProvider(
            model=model,
            default_reply=default_reply,
            replies=replies,
        )

    if normalized in {"openai", "openai_compat"}:
        from openai_compat import OpenAICompatProvider

        return OpenAICompatProvider(
            base_url,
            api_key,
            model=model,
            timeout=timeout,
            transport=transport,
        )

    raise ProviderError(f"unknown provider kind: {normalized}")
