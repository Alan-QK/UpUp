"""Day 15 手工运行入口：多轮对话 CLI（支持 /reset /exit，可用 --demo 离线）。"""

from __future__ import annotations

import argparse
import json
import os
import sys

import httpx

from chat_client import ChatClient
from chat_session import ChatSession
from persona_assistant import PersonaAssistant

DEFAULT_PERSONA = (
    "你是一名资深前端转 AI Agent 的学习助教。"
    "回答简洁、偏实战，必要时用前端类比解释 Python/LLM 概念。"
)


def _mask(secret: str) -> str:
    if len(secret) <= 8:
        return "***"
    return f"{secret[:3]}***{secret[-4:]}"


def demo_transport() -> httpx.MockTransport:
    """离线 Demo：根据历史轮数回固定风格回复。"""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        messages = body.get("messages") or []
        user_text = ""
        turns = 0
        for m in messages:
            if m.get("role") == "user":
                turns += 1
                user_text = str(m.get("content") or "")
        reply = f"[demo·第{turns}轮] {user_text[:80]}"
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-demo",
                "model": body.get("model") or "demo-model",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": reply},
                    }
                ],
                "usage": {
                    "prompt_tokens": max(1, len(user_text) // 4),
                    "completion_tokens": max(1, len(reply) // 4),
                    "total_tokens": max(2, (len(user_text) + len(reply)) // 4),
                },
            },
        )

    return httpx.MockTransport(handler)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Day 15 · 多轮对话 CLI")
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
        "--line",
        action="append",
        dest="lines",
        default=None,
        help="非交互模式：按顺序处理多条输入（可重复）；最后建议加 /exit",
    )
    return p


def _print_reply(reply) -> None:
    if reply.kind == "assistant":
        print(f"assistant> {reply.message}")
    else:
        print(f"system   > {reply.message}")


def run_session(session: ChatSession, lines: list[str] | None) -> int:
    if lines is not None:
        for line in lines:
            print(f"you      > {line}")
            reply = session.handle_line(line)
            _print_reply(reply)
            if reply.should_exit:
                return 0
        return 0

    print("进入多轮对话。输入 /help 查看命令，/exit 退出。")
    while True:
        try:
            line = input("you      > ")
        except (EOFError, KeyboardInterrupt):
            print()
            print("system   > 再见。")
            return 0
        reply = session.handle_line(line)
        _print_reply(reply)
        if reply.should_exit:
            return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.demo:
        base_url = "https://api.test/v1"
        api_key = "sk-demo"
        model = "demo-model"
        transport = demo_transport()
        print("mode       : demo (MockTransport)")
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        base_url = os.environ.get(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        ).strip()
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()
        if not api_key:
            print(
                "缺少 OPENAI_API_KEY。可先：python3 main.py --demo "
                '--line "你好" --line /history --line /exit',
                file=sys.stderr,
            )
            return 2
        transport = None
        print("mode       : live")
        print(f"base_url   : {base_url}")
        print(f"model      : {model}")
        print(f"api_key    : {_mask(api_key)}")

    print(f"persona    : {args.persona[:60]}...")
    print("---")

    with ChatClient(
        base_url,
        api_key,
        model=model,
        transport=transport,
    ) as client:
        bot = PersonaAssistant(client, system_prompt=args.persona)
        session = ChatSession(bot)
        return run_session(session, args.lines)


if __name__ == "__main__":
    raise SystemExit(main())
