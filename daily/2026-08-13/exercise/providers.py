"""Day 18 练习：ChatProvider 协议、假实现与工厂。

请完成 TODO，使 tests/ 全部通过。
"""

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
    def name(self) -> str:
        """实现名称，如 fake / openai_compat。"""
        ...

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float | None = None,
        top_p: float | None = None,
    ) -> ChatCompletionResult:
        """根据消息列表生成一条 assistant 回复。"""
        ...

    def close(self) -> None:
        """释放底层资源（无资源也可空实现）。"""
        ...


def last_user_content(messages: Sequence[ChatMessage]) -> str:
    """从后往前找第一条 role == 'user' 的 content；找不到返回空串。"""
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    return ""


class FakeChatProvider:
    """离线假实现：查表回复 + 记录调用。

    构造参数：
    - model: 写入 ChatCompletionResult.model
    - default_reply: 查表未命中时的回复
    - replies: 「最后一条 user 文本」→ 回复 的映射

    complete 规则：
    - messages 为空 → ProviderError("messages must not be empty")
    - 用 last_user_content(messages) 查 replies；命中用表内值，否则 default_reply
    - 把本次入参追加到 self.calls（messages 转成 tuple 快照）
    - finish_reason 固定 "stop"
    - prompt_tokens = 所有 message.content 的字符数之和
    - completion_tokens = 回复的字符数
    - total_tokens = 二者相加
    - temperature / top_p 今天不改变回复内容，但必须记入 ProviderCall

    close：空操作即可。
    name 属性：固定返回 "fake"
    """

    def __init__(
        self,
        *,
        model: str = "fake-model",
        default_reply: str = "（假模型默认回复）",
        replies: Mapping[str, str] | None = None,
    ) -> None:
        # TODO: 保存参数；self.calls: list[ProviderCall] = []
        raise NotImplementedError

    @property
    def name(self) -> str:
        # TODO
        raise NotImplementedError

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float | None = None,
        top_p: float | None = None,
    ) -> ChatCompletionResult:
        # TODO
        raise NotImplementedError

    def close(self) -> None:
        # TODO: 允许空实现
        raise NotImplementedError


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
    """按 kind 创建 Provider。

    规则：
    - kind 先 strip，再 lower；空串 → ProviderError("provider kind must not be empty")
    - "fake" → FakeChatProvider(model=..., default_reply=..., replies=...)
    - "openai" 或 "openai_compat" → OpenAICompatProvider(
          base_url=..., api_key=..., model=..., timeout=..., transport=...
      )
      （从 openai_compat 延迟导入，避免循环依赖）
    - 其他 → ProviderError("unknown provider kind: {kind}")
    """
    # TODO: 实现这里
    raise NotImplementedError
