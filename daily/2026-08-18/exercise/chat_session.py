"""Day 20 复用：斜杠命令会话层（Day 15 完成版，适配流式助手）。

本文件已给齐。今日重点实现 streaming_assistant.py。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Protocol

from streaming_client import ChatClientError, ChatMessage


class AssistantLike(Protocol):
    def ask(self, user_text: str, *, temperature: float | None = None) -> str: ...

    def ask_stream(
        self, user_text: str, *, temperature: float | None = None
    ) -> Iterator[str]: ...

    def reset(self) -> None: ...

    def history(self) -> list[ChatMessage]: ...


@dataclass(frozen=True)
class SessionReply:
    """处理一行输入后的结果，供 CLI 打印与决定是否退出。"""

    kind: str
    message: str
    should_exit: bool = False
    already_printed: bool = False


class ChatSession:
    """把「斜杠命令 + 普通聊天」收成可单测的会话层。"""

    HELP_TEXT = (
        "可用命令：\n"
        "/help     显示帮助\n"
        "/reset    清空多轮历史（人设保留）\n"
        "/history  显示当前历史摘要\n"
        "/exit     退出（/quit 同义）"
    )

    def __init__(self, assistant: AssistantLike) -> None:
        self._assistant = assistant

    @property
    def assistant(self) -> AssistantLike:
        return self._assistant

    def handle_line(self, line: str) -> SessionReply:
        text = line.strip()
        if not text:
            return SessionReply(kind="system", message="（空输入已忽略）")

        if text.startswith("/"):
            return self._handle_command(text)

        try:
            reply = self._assistant.ask(text)
        except ChatClientError as exc:
            return SessionReply(kind="system", message=f"调用失败：{exc}")
        return SessionReply(kind="assistant", message=reply)

    def _handle_command(self, text: str) -> SessionReply:
        cmd = text.split(maxsplit=1)[0].lower()

        if cmd == "/help":
            return SessionReply(kind="system", message=self.HELP_TEXT)

        if cmd == "/reset":
            self._assistant.reset()
            return SessionReply(kind="system", message="已清空对话历史。")

        if cmd == "/history":
            return SessionReply(kind="system", message=self._format_history())

        if cmd in {"/exit", "/quit"}:
            return SessionReply(kind="exit", message="再见。", should_exit=True)

        return SessionReply(
            kind="system",
            message=f"未知命令：{cmd}。输入 /help 查看帮助。",
        )

    def _format_history(self) -> str:
        history = self._assistant.history()
        if not history:
            return "当前没有历史消息。"

        lines = [f"当前历史共 {len(history)} 条消息："]
        for msg in history:
            content = msg.content
            if len(content) > 80:
                content = content[:80] + "..."
            lines.append(f"[{msg.role}] {content}")
        return "\n".join(lines)
