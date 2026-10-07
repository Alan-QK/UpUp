"""Day 18 手工运行入口：用工厂切换 fake / openai Provider。"""

from __future__ import annotations

import argparse
import json
import os
import sys

import httpx

from providers import ChatMessage, create_chat_provider


DEFAULT_QUESTION = "一句话解释什么是 ChatProvider？"


def _mask(secret: str) -> str:
    if len(secret) <= 8:
        return "***"
    return f"{secret[:3]}***{secret[-4:]}"


def demo_transport() -> httpx.MockTransport:
    """真 openai 路径的离线 Mock（验证工厂能创建 openai_compat）。"""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        messages = body.get("messages") or []
        last_user = ""
        for item in reversed(messages):
            if isinstance(item, dict) and item.get("role") == "user":
                last_user = str(item.get("content") or "")
                break
        reply = f"[mock-openai] 收到：{last_user}"
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
                    "prompt_tokens": 12,
                    "completion_tokens": max(1, len(reply) // 4),
                    "total_tokens": 12 + max(1, len(reply) // 4),
                },
            },
        )

    return httpx.MockTransport(handler)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 18 · Provider 抽象 Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="使用 fake Provider（默认查表 + 默认回复）",
    )
    parser.add_argument(
        "--provider",
        default="",
        help="覆盖 Provider 种类：fake / openai（--demo 时默认 fake）",
    )
    parser.add_argument(
        "-m",
        "--message",
        default=DEFAULT_QUESTION,
        help="用户问题",
    )
    parser.add_argument(
        "--mock-openai",
        action="store_true",
        help="openai 路径使用 MockTransport，不访问外网",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    kind = (args.provider or ("fake" if args.demo else "openai")).strip().lower()

    system = ChatMessage(
        role="system",
        content="你是简洁的助教，用一两句话回答。",
    )
    user = ChatMessage(role="user", content=args.message)
    messages = [system, user]

    if kind == "fake":
        provider = create_chat_provider(
            "fake",
            model="fake-day18",
            default_reply="ChatProvider 就是「能 complete 的聊天后端接口」。",
            replies={
                DEFAULT_QUESTION: (
                    "ChatProvider 是可替换的聊天补全接口："
                    "业务只调用 complete，Fake/OpenAI 都可插拔。"
                ),
            },
        )
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "").strip() or "demo-key"
        base_url = (
            os.environ.get("OPENAI_BASE_URL", "").strip()
            or "https://api.openai.com/v1"
        )
        model = os.environ.get("OPENAI_MODEL", "").strip() or "gpt-4o-mini"
        transport = demo_transport() if (args.demo or args.mock_openai) else None
        if transport is None and api_key == "demo-key":
            print(
                "缺少 OPENAI_API_KEY。可用：python3 main.py --demo",
                file=sys.stderr,
            )
            return 2
        print(f"openai key : {_mask(api_key)}")
        print(f"base_url   : {base_url}")
        print(f"model      : {model}")
        provider = create_chat_provider(
            kind,
            model=model,
            api_key=api_key,
            base_url=base_url,
            transport=transport,
        )

    try:
        print(f"provider   : {provider.name}")
        result = provider.complete(messages, temperature=0.2)
        print(f"model      : {result.model}")
        print(f"tokens     : prompt={result.prompt_tokens} "
              f"completion={result.completion_tokens} total={result.total_tokens}")
        print("---")
        print(result.content)
    finally:
        provider.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
