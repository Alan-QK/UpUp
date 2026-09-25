"""Day 12 参考实现：角色化多轮助手。"""

from __future__ import annotations

from chat_client import ChatClient, ChatMessage


class PersonaAssistant:
    """带固定人设的多轮对话助手。"""

    def __init__(self, client: ChatClient, *, system_prompt: str) -> None:
        prompt = system_prompt.strip()
        if not prompt:
            raise ValueError("empty system_prompt")
        self._client = client
        self._system_prompt = prompt
        self._history: list[ChatMessage] = []

    def ask(
        self,
        user_text: str,
        *,
        temperature: float | None = None,
    ) -> str:
        text = user_text.strip()
        if not text:
            raise ValueError("empty user_text")

        user_msg = ChatMessage(role="user", content=text)
        messages = [
            ChatMessage(role="system", content=self._system_prompt),
            *self._history,
            user_msg,
        ]
        result = self._client.complete(messages, temperature=temperature)
        assistant_msg = ChatMessage(role="assistant", content=result.content)
        self._history.append(user_msg)
        self._history.append(assistant_msg)
        return result.content

    def reset(self) -> None:
        self._history.clear()

    def history(self) -> list[ChatMessage]:
        return list(self._history)
