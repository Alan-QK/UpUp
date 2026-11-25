"""Day 20 手工运行入口：Phase 1 里程碑 cli-chatbot。

整合：.env 密钥、流式输出、滑动窗口、斜杠命令会话。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

from chat_session import ChatSession, SessionReply
from env_loader import load_dotenv, load_llm_settings, mask_secret
from streaming_assistant import StreamingWindowedAssistant
from streaming_client import ChatClientError, StreamingChatClient, print_stream

DEFAULT_PERSONA = (
    "你是一名资深前端转 AI Agent 的学习助教。"
    "回答简洁、偏实战，必要时用前端类比解释 Python/LLM 概念。"
)

SAMPLE_ENV = Path(__file__).with_name("sample.env")


def demo_transport() -> httpx.MockTransport:
    """离线 Demo：按字符拆 SSE，模拟打字机效果。"""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        messages = body.get("messages") or []
        user_text = ""
        turns = 0
        for m in messages:
            if m.get("role") == "user":
                turns += 1
                user_text = str(m.get("content") or "")
        reply = f"[demo·stream·第{turns}轮] {user_text[:60]}"
        chunks: list[dict] = [
            {
                "id": "chatcmpl-demo",
                "choices": [{"index": 0, "delta": {"role": "assistant"}}],
            }
        ]
        for ch in reply:
            chunks.append(
                {
                    "id": "chatcmpl-demo",
                    "choices": [{"index": 0, "delta": {"content": ch}}],
                }
            )
        chunks.append(
            {
                "id": "chatcmpl-demo",
                "model": body.get("model") or "demo-model",
                "choices": [
                    {"index": 0, "delta": {}, "finish_reason": "stop"}
                ],
            }
        )
        parts = [
            f"data: {json.dumps(obj, ensure_ascii=False)}\n\n" for obj in chunks
        ]
        parts.append("data: [DONE]\n\n")
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content="".join(parts).encode("utf-8"),
        )

    return httpx.MockTransport(handler)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Day 20 · cli-chatbot 里程碑")
    p.add_argument(
        "--demo",
        action="store_true",
        help="使用 MockTransport，不访问外网",
    )
    p.add_argument(
        "--persona",
        default=DEFAULT_PERSONA,
        help="system 人设文本",
    )
    p.add_argument(
        "--max-turns",
        type=int,
        default=6,
        help="本地历史最多保留几轮完整对话",
    )
    p.add_argument(
        "--env-file",
        default="",
        help="可选：加载指定 .env（默认不强制；demo 模式不需要）",
    )
    p.add_argument(
        "--no-stream-print",
        action="store_true",
        help="关闭终端打字机效果（仍走流式 API，只是整段打印）",
    )
    p.add_argument(
        "--line",
        action="append",
        dest="lines",
        default=None,
        help="非交互模式：按顺序处理多条输入（可重复）；最后建议加 /exit",
    )
    return p


def _print_reply(reply: SessionReply) -> None:
    if reply.already_printed:
        return
    if reply.kind == "assistant":
        print(f"assistant> {reply.message}")
    else:
        print(f"system   > {reply.message}")


def _handle_line_streaming(
    session: ChatSession,
    line: str,
    *,
    stream_print: bool,
) -> SessionReply:
    text = line.strip()
    if (not text) or text.startswith("/"):
        return session.handle_line(line)

    assistant = session.assistant
    try:
        if stream_print:
            print("assistant> ", end="", flush=True)
            msg = print_stream(assistant.ask_stream(text))
            return SessionReply(
                kind="assistant",
                message=msg,
                already_printed=True,
            )
        msg = assistant.ask(text)
        return SessionReply(kind="assistant", message=msg)
    except ChatClientError as exc:
        return SessionReply(kind="system", message=f"调用失败：{exc}")


def run_session(
    session: ChatSession,
    lines: list[str] | None,
    *,
    stream_print: bool,
) -> int:
    if lines is not None:
        for line in lines:
            print(f"you      > {line}")
            reply = _handle_line_streaming(
                session, line, stream_print=stream_print
            )
            _print_reply(reply)
            if reply.should_exit:
                return 0
        return 0

    print("进入 cli-chatbot。输入 /help 查看命令，/exit 退出。")
    while True:
        try:
            line = input("you      > ")
        except (EOFError, KeyboardInterrupt):
            print()
            print("system   > 再见。")
            return 0
        reply = _handle_line_streaming(session, line, stream_print=stream_print)
        _print_reply(reply)
        if reply.should_exit:
            return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    env_path = Path(args.env_file) if args.env_file else SAMPLE_ENV
    if env_path.is_file() and not args.demo:
        load_dotenv(env_path, override=False)

    if args.demo:
        base_url = "https://api.test/v1"
        api_key = "sk-demo"
        model = "demo-model"
        transport = demo_transport()
        print("mode       : demo (MockTransport)")
    else:
        try:
            settings = load_llm_settings()
        except Exception as exc:  # EnvError
            print(
                f"配置错误：{exc}\n"
                "可先：python3 main.py --demo --line \"你好\" --line /exit\n"
                "或设置 OPENAI_API_KEY（可复制 sample.env 为 .env）",
                file=sys.stderr,
            )
            return 2
        base_url = settings.base_url
        api_key = settings.api_key
        model = settings.model
        transport = None
        print("mode       : live")
        print(f"base_url   : {base_url}")
        print(f"model      : {model}")
        print(f"api_key    : {mask_secret(api_key)}")

    # --line 批跑默认整段打印，避免与脚本断言打架；交互默认打字机
    stream_print = (not args.no_stream_print) and (args.lines is None)

    print(f"persona    : {args.persona[:60]}...")
    print(f"max_turns  : {args.max_turns}")
    print(f"stream_ui  : {stream_print}")
    print("---")

    with StreamingChatClient(
        base_url,
        api_key,
        model=model,
        transport=transport,
    ) as client:
        bot = StreamingWindowedAssistant(
            client,
            system_prompt=args.persona,
            max_turns=args.max_turns,
        )
        session = ChatSession(bot)
        return run_session(session, args.lines, stream_print=stream_print)


if __name__ == "__main__":
    raise SystemExit(main())
