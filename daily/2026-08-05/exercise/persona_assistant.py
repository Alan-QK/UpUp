"""Day 12 练习：角色化多轮助手（固定 system 人设 + 会话历史）。

请完成 TODO，使 tests/ 全部通过。
依赖：同目录下已给齐的 chat_client.py（Day 11）。
"""

from __future__ import annotations

from chat_client import ChatClient, ChatMessage


class PersonaAssistant:
    """带固定人设的多轮对话助手。

    约定：
    - 构造时传入非空 system_prompt（人设/规则）
    - ask(user_text) 每次把「system + 历史 + 本轮 user」发给模型
    - 成功后把本轮 user 与 assistant 追加进内部历史
    - reset() 清空历史，但保留人设
    - history() 返回历史副本（不含 system）；修改返回值不影响内部状态
    """

    def __init__(self, client: ChatClient, *, system_prompt: str) -> None:
        # TODO: 校验 system_prompt.strip() 非空，否则 ValueError("empty system_prompt")
        #       保存 client、system_prompt（建议存 strip 后的文本）、内部历史列表
        raise NotImplementedError

    def ask(
        self,
        user_text: str,
        *,
        temperature: float | None = None,
    ) -> str:
        """发送一轮用户消息，返回助手回复文本。

        步骤：
        1. user_text.strip() 为空 → ValueError("empty user_text")
        2. 组装 messages = [system] + history + [本轮 user]
        3. 调用 client.complete(messages, temperature=...)
        4. 把本轮 user 与 assistant 消息追加到历史
        5. 返回 result.content
        """
        # TODO: 实现这里
        raise NotImplementedError

    def reset(self) -> None:
        """清空多轮历史；人设不变。"""
        # TODO: 实现这里
        raise NotImplementedError

    def history(self) -> list[ChatMessage]:
        """返回当前历史（user/assistant）的浅拷贝列表。"""
        # TODO: 实现这里
        raise NotImplementedError
