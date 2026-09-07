"""Day 20 复用：滑动窗口历史裁剪（Day 16 精简版）。

本文件已给齐。今日重点实现 streaming_assistant.py。
"""

from __future__ import annotations

from typing import Sequence

from streaming_client import ChatMessage


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
