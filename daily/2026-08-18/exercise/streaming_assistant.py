"""Day 20 练习：流式 + 滑动窗口助手（Phase 1 里程碑核心）。

请完成 TODO，使 tests/ 全部通过。
"""

from __future__ import annotations

from collections.abc import Iterator

from history_window import sliding_window
from streaming_client import ChatMessage, StreamingChatClient


class StreamingWindowedAssistant:
    """固定人设 + 流式补全 + 本地历史滑动窗口。

    约定：
    - system 人设常驻，不进入 history()
    - history 只保留最近 max_turns 个完整 user/assistant 轮
    - ask_stream：边 yield 增量文本，流结束后再写入历史
    - ask：等价于 "".join(ask_stream(...))
    """

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
        """流式提问：yield 增量；全部消费完后才更新本地历史。

        规则：
        - user_text strip 后为空 → ValueError("empty user_text")
        - 请求消息 = [system] + sliding_window(history, max_turns) + [user]
        - 用 client.iter_content 产出增量；调用方必须把迭代器消费完
        - 拼接完整回复后：append user、append assistant，再对 history 做滑动窗口
        - 若 iter_content 中途抛错：不要写入本轮历史
        """
        # TODO: 实现这里
        raise NotImplementedError

    def ask(
        self,
        user_text: str,
        *,
        temperature: float | None = None,
    ) -> str:
        """非流式外观：收集 ask_stream 的全部增量并返回。"""
        # TODO: 实现这里
        raise NotImplementedError

    def reset(self) -> None:
        """清空多轮历史（人设保留）。"""
        # TODO: 实现这里
        raise NotImplementedError

    def history(self) -> list[ChatMessage]:
        """返回历史副本（不含 system）。"""
        # TODO: 实现这里
        raise NotImplementedError
