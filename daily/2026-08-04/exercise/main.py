"""Day 11 手工运行入口：非流式 Chat Completions（支持 --demo 离线）。"""

from __future__ import annotations

import argparse
import json
import os
import sys

import httpx

from chat_client import ChatClient, ChatMessage


def _mask(secret: str) -> str:
    if len(secret) <= 8:
        return "***"
    return f"{secret[:3]}***{secret[-4:]}"


def demo_transport() -> httpx.MockTransport:
    """离线 Demo：不访问外网，按提示词回一段固定风格回复。"""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        user_text = ""
        for m in body.get("messages") or []:
            if m.get("role") == "user":
                user_text = str(m.get("content") or "")
        reply = (
            f"[demo] 收到：{user_text[:80]}"
            if user_text
            else "[demo] （空提示）"
        )
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
    p = argparse.ArgumentParser(description="Day 11 · 第一次 Chat Completions")
    p.add_argument(
        "-m",
        "--message",
        default="用一句话介绍什么是 AI Agent",
        help="发给模型的用户消息",
    )
    p.add_argument(
        "--demo",
        action="store_true",
        help="使用 MockTransport，不访问外网",
    )
    p.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="可选 temperature",
    )
    return p


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
                "缺少 OPENAI_API_KEY。可先：python3 main.py --demo",
                file=sys.stderr,
            )
            return 2
        transport = None
        print("mode       : live")
        print(f"base_url   : {base_url}")
        print(f"model      : {model}")
        print(f"api_key    : {_mask(api_key)}")

    messages = [ChatMessage(role="user", content=args.message)]
    with ChatClient(
        base_url,
        api_key,
        model=model,
        transport=transport,
    ) as client:
        result = client.complete(messages, temperature=args.temperature)

    print(f"assistant  : {result.content}")
    if result.total_tokens is not None:
        print(
            f"usage      : prompt={result.prompt_tokens} "
            f"completion={result.completion_tokens} "
            f"total={result.total_tokens}"
        )
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
