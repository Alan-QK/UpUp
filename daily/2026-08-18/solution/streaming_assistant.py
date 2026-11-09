"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

from collections.abc import Iterator

from history_window import sliding_window
from streaming_client import ChatMessage, StreamingChatClient


class StreamingWindowedAssistant:
    """固定人设 + 流式补全 + 本地历史滑动窗口。"""

    def __init__(
        self,
        client: StreamingChatClient,
        *,
        system_prompt: str,
        max_turns: int = 6,
    ) -> None:
        prompt = system_prompt.strip()
        if not prompt:
            raise ValueError("empty system_prompt")
        if max_turns < 1:
            raise ValueError("max_turns must be >= 1")
        self._client = client
        self._system_prompt = prompt
        self._max_turns = max_turns
        self._history: list[ChatMessage] = []

    @property
    def max_turns(self) -> int:
        return self._max_turns

    def ask_stream(
        self,
        user_text: str,
        *,
        temperature: float | None = None,
    ) -> Iterator[str]:
        text = user_text.strip()
        if not text:
            raise ValueError("empty user_text")

        user_msg = ChatMessage(role="user", content=text)
        trimmed = sliding_window(self._history, max_turns=self._max_turns)
        messages = [
            ChatMessage(role="system", content=self._system_prompt),
            *trimmed,
            user_msg,
        ]

        parts: list[str] = []
        for chunk in self._client.iter_content(messages, temperature=temperature):
            parts.append(chunk)
            yield chunk

        assistant_msg = ChatMessage(role="assistant", content="".join(parts))
        self._history.append(user_msg)
        self._history.append(assistant_msg)
        self._history = sliding_window(self._history, max_turns=self._max_turns)

    def ask(
        self,
        user_text: str,
        *,
        temperature: float | None = None,
    ) -> str:
        return "".join(self.ask_stream(user_text, temperature=temperature))

    def reset(self) -> None:
        self._history.clear()

    def history(self) -> list[ChatMessage]:
        return list(self._history)
