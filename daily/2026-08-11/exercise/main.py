"""Day 16 手工运行入口：观察滑动窗口如何裁掉旧轮次。"""

from __future__ import annotations

import argparse
import json
import os
import sys

import httpx

from chat_client import ChatClient
from history_window import WindowedAssistant, count_turns

DEFAULT_PERSONA = (
    "你是一名资深前端转 AI Agent 的学习助教。"
    "回答简洁；提到上下文时说明你还记得哪些轮。"
)


def _mask(secret: str) -> str:
    if len(secret) <= 8:
        return "***"
    return f"{secret[:3]}***{secret[-4:]}"


def demo_transport() -> httpx.MockTransport:
    """离线 Demo：回复里带上「请求里看到的历史轮数」，方便对照窗口。"""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        messages = body.get("messages") or []
        prior_users = [m for m in messages if m.get("role") == "user"]
        # 最后一条 user 是本轮；之前的 user 数 = 窗口内历史轮数
        window_turns = max(0, len(prior_users) - 1)
        user_text = str(prior_users[-1].get("content") or "") if prior_users else ""
        remembered = [
            str(m.get("content") or "")[:20]
            for m in prior_users[:-1]
        ]
        mem = ",".join(remembered) if remembered else "（无）"
        reply = (
            f"[demo·窗口内历史{window_turns}轮·记得:{mem}] "
            f"{user_text[:60]}"
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
                    "prompt_tokens": max(1, len(json.dumps(messages)) // 4),
                    "completion_tokens": max(1, len(reply) // 4),
                    "total_tokens": max(2, (len(json.dumps(messages)) + len(reply)) // 4),
                },
            },
        )

    return httpx.MockTransport(handler)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Day 16 · 滑动窗口历史裁剪")
    p.add_argument(
        "-m",
        "--message",
        action="append",
        dest="messages",
        default=None,
        help="用户消息；可重复传入以模拟多轮",
    )
    p.add_argument(
        "--max-turns",
        type=int,
        default=2,
        help="滑动窗口保留的最大轮数（默认 2）",
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
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    messages = args.messages or [
        "第一轮：我叫小前端",
        "第二轮：我在学 Agent",
        "第三轮：我刚才说我叫什么？",
        "第四轮：我在学什么？",
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

    print(f"max_turns  : {args.max_turns}")
    print(f"persona    : {args.persona[:60]}...")
    print("---")

    with ChatClient(
        base_url,
        api_key,
        model=model,
        transport=transport,
    ) as client:
        bot = WindowedAssistant(
            client,
            system_prompt=args.persona,
            max_turns=args.max_turns,
        )
        for i, text in enumerate(messages, start=1):
            print(f"user[{i}]   : {text}")
            reply = bot.ask(text)
            print(f"assistant : {reply}")
            print(
                f"stored    : {len(bot.history())} msgs / "
                f"{count_turns(bot.history())} turns"
            )
            print("---")

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
