"""Day 12 手工运行入口：角色化多轮助手（支持 --demo 离线）。"""

from __future__ import annotations

import argparse
import json
import os
import sys

import httpx

from chat_client import ChatClient
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
    """离线 Demo：根据历史轮数回固定风格回复，便于观察多轮上下文。"""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        messages = body.get("messages") or []
        system = ""
        user_text = ""
        turns = 0
        for m in messages:
            role = m.get("role")
            if role == "system" and not system:
                system = str(m.get("content") or "")
            elif role == "user":
                turns += 1
                user_text = str(m.get("content") or "")
        persona_tag = "助教" if "助教" in system else "助手"
        reply = f"[demo·{persona_tag}·第{turns}轮] {user_text[:80]}"
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
    p = argparse.ArgumentParser(description="Day 12 · 角色化多轮助手")
    p.add_argument(
        "-m",
        "--message",
        action="append",
        dest="messages",
        default=None,
        help="用户消息；可重复传入以模拟多轮（默认两轮示例）",
    )
    p.add_argument(
        "--persona",
        default=DEFAULT_PERSONA,
        help="system 人设文本",
    )
    p.add_argument(
        "--demo",
        action="store_true",
        help="使用 MockTransport，不访问外网",
    )
    p.add_argument(
        "--reset-between",
        action="store_true",
        help="在每条 -m 之间调用 reset（对比「有无历史」）",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    messages = args.messages or [
        "用前端的 fetch 类比一下 Chat Completions",
        "那多轮对话的 messages 该怎么拼？",
    ]

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
                "缺少 OPENAI_API_KEY。可先：python3 main.py --demo",
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
        for i, text in enumerate(messages, start=1):
            if args.reset_between and i > 1:
                bot.reset()
                print("(reset)")
            print(f"user[{i}]   : {text}")
            reply = bot.ask(text)
            print(f"assistant : {reply}")
            print(f"history   : {len(bot.history())} msgs")
            print("---")

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
