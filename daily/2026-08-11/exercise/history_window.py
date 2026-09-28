"""Day 16 练习：滑动窗口历史裁剪。

请完成 TODO，使 tests/ 全部通过。
依赖：同目录下已给齐的 chat_client.py。
"""

from __future__ import annotations

from typing import Sequence

from chat_client import ChatClient, ChatMessage


def count_turns(history: Sequence[ChatMessage]) -> int:
    """统计完整对话轮数（一对 user+assistant = 1 轮）。

    约定：只统计 role 为 user / assistant 的消息；其它 role 忽略。
    从左到右按「user 后紧跟 assistant」配对；不成对的尾部 user 不计入。
    """
    # TODO
    raise NotImplementedError


def sliding_window(
    history: Sequence[ChatMessage],
    *,
    max_turns: int,
) -> list[ChatMessage]:
    """保留最近 max_turns 轮完整对话，丢掉更早的轮次。

    规则：
    - max_turns < 1 → ValueError("max_turns must be >= 1")
    - 只保留 user/assistant；忽略 system 等其它角色（system 应由调用方单独放）
    - 按完整轮（user+assistant）从**末尾**截取
    - 返回新 list，不修改入参
    """
    # TODO
    raise NotImplementedError


class WindowedAssistant:
    """带滑动窗口的多轮助手：人设常驻，历史只保留最近 N 轮。

    与 Day 12 PersonaAssistant 的差异：
    - 构造时多一个 max_turns
    - 每次 ask：先对已有历史做 sliding_window，再拼 system + 窗口 + 本轮 user
    - 收到回复后追加历史，并再次 sliding_window，避免内存无限增长
    """

    def __init__(
        self,
        client: ChatClient,
        *,
        system_prompt: str,
        max_turns: int = 3,
    ) -> None:
        # TODO:
        # - system_prompt strip 后为空 → ValueError("empty system_prompt")
        # - max_turns < 1 → ValueError("max_turns must be >= 1")
        # - 保存 client / system_prompt / max_turns / 空 history
        raise NotImplementedError

    @property
    def max_turns(self) -> int:
        # TODO: 返回窗口大小
        raise NotImplementedError

    def ask(
        self,
        user_text: str,
        *,
        temperature: float | None = None,
    ) -> str:
        """发起一轮对话；请求体只带窗口内历史。"""
        # TODO:
        # 1. user_text strip 后为空 → ValueError("empty user_text")
        # 2. trimmed = sliding_window(self._history, max_turns=self._max_turns)
        # 3. messages = [system, *trimmed, 本轮 user]
        # 4. complete → 追加 user/assistant 到 history
        # 5. self._history = sliding_window(self._history, max_turns=self._max_turns)
        # 6. 返回 assistant 文本
        raise NotImplementedError

    def reset(self) -> None:
        """清空多轮历史（人设与 max_turns 保留）。"""
        # TODO
        raise NotImplementedError

    def history(self) -> list[ChatMessage]:
        """返回当前（已裁剪后的）历史副本。"""
        # TODO
        raise NotImplementedError
