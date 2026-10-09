"""Day 15 练习：多轮对话会话层（斜杠命令 + 普通聊天）。

请完成 TODO，使 tests/ 全部通过。
依赖：同目录下已给齐的 chat_client.py / persona_assistant.py。
"""

from __future__ import annotations

from dataclasses import dataclass

from chat_client import ChatClientError
from persona_assistant import PersonaAssistant


@dataclass(frozen=True)
class SessionReply:
    """处理一行输入后的结果，供 CLI 打印与决定是否退出。"""

    kind: str
    """结果类型：assistant / system / exit。"""

    message: str
    """要展示给用户的文本。"""

    should_exit: bool = False
    """为 True 时，CLI 应结束 REPL 循环。"""


class ChatSession:
    """把「斜杠命令 + 普通聊天」收成可单测的会话层。

    约定：
    - 空输入（strip 后为空）→ system 提示，不调用模型
    - `/help` → 帮助文本
    - `/reset` → 清空历史，人设保留
    - `/history` → 打印当前历史摘要
    - `/exit` 或 `/quit` → 退出（should_exit=True）
    - 未知 `/xxx` → system 提示未知命令
    - 其它文本 → 交给 PersonaAssistant.ask
    - ChatClientError → 捕获为 system 错误信息，不向外抛
    """

    HELP_TEXT = (
        "可用命令：\n"
        "/help     显示帮助\n"
        "/reset    清空多轮历史（人设保留）\n"
        "/history  显示当前历史摘要\n"
        "/exit     退出（/quit 同义）"
    )

    def __init__(self, assistant: PersonaAssistant) -> None:
        # TODO: 保存 assistant
        raise NotImplementedError

    def handle_line(self, line: str) -> SessionReply:
        """处理用户输入的一行（命令或聊天内容）。"""
        # TODO:
        # 1. text = line.strip()；空 → SessionReply(kind="system", message="（空输入已忽略）")
        # 2. 若 text 以 "/" 开头 → 走 _handle_command
        # 3. 否则 try: assistant.ask(text) → SessionReply(kind="assistant", message=reply)
        #    except ChatClientError as exc → SessionReply(kind="system", message=f"调用失败：{exc}")
        raise NotImplementedError

    def _handle_command(self, text: str) -> SessionReply:
        """处理以 / 开头的命令（text 已 strip）。

        命令名大小写不敏感；只认第一个 token 为命令。
        """
        # TODO:
        # - 拆出 cmd = text.split(maxsplit=1)[0].lower()
        # - /help → kind="system", message=HELP_TEXT
        # - /reset → assistant.reset()；message="已清空对话历史。"
        # - /history → 调用 _format_history()
        # - /exit 或 /quit → kind="exit", message="再见。", should_exit=True
        # - 其它 → kind="system", message=f"未知命令：{cmd}。输入 /help 查看帮助。"
        raise NotImplementedError

    def _format_history(self) -> str:
        """把 assistant.history() 格式化成可读摘要。"""
        # TODO:
        # - 空历史 → "当前没有历史消息。"
        # - 否则首行 "当前历史共 N 条消息："，随后每行 "[role] content"
        #   content 超过 80 字符时截断并加 "..."
        raise NotImplementedError
