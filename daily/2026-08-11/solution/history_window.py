"""Day 16 参考实现：滑动窗口历史裁剪。"""

from __future__ import annotations

from typing import Sequence

from chat_client import ChatClient, ChatMessage


def _complete_pairs(history: Sequence[ChatMessage]) -> list[ChatMessage]:
    """从左到右抽出完整的 user+assistant 轮次（扁平 list）。"""
    pairs: list[ChatMessage] = []
    i = 0
    n = len(history)
    while i < n:
        msg = history[i]
        if msg.role not in ("user", "assistant"):
            i += 1
            continue
        if msg.role == "user" and i + 1 < n and history[i + 1].role == "assistant":
            pairs.append(msg)
            pairs.append(history[i + 1])
            i += 2
            continue
        # 不成对的 user / 落单的 assistant：跳过该条，继续找
        i += 1
    return pairs


def count_turns(history: Sequence[ChatMessage]) -> int:
    """统计完整对话轮数（一对 user+assistant = 1 轮）。"""
    return len(_complete_pairs(history)) // 2


def sliding_window(
    history: Sequence[ChatMessage],
    *,
    max_turns: int,
) -> list[ChatMessage]:
    """保留最近 max_turns 轮完整对话，丢掉更早的轮次。"""
    if max_turns < 1:
        raise ValueError("max_turns must be >= 1")
    pairs = _complete_pairs(history)
    keep = max_turns * 2
    if len(pairs) <= keep:
        return list(pairs)
    return pairs[-keep:]


class WindowedAssistant:
    """带滑动窗口的多轮助手：人设常驻，历史只保留最近 N 轮。"""

    def __init__(
        self,
        client: ChatClient,
        *,
        system_prompt: str,
        max_turns: int = 3,
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
        trimmed = sliding_window(self._history, max_turns=self._max_turns)
        messages = [
            ChatMessage(role="system", content=self._system_prompt),
            *trimmed,
            user_msg,
        ]
        result = self._client.complete(messages, temperature=temperature)
        assistant_msg = ChatMessage(role="assistant", content=result.content)
        self._history.append(user_msg)
        self._history.append(assistant_msg)
        self._history = sliding_window(self._history, max_turns=self._max_turns)
        return result.content

    def reset(self) -> None:
        self._history.clear()

    def history(self) -> list[ChatMessage]:
        return list(self._history)
