"""Day 13 手工运行入口：流式 Chat Completions（支持 --demo 离线）。"""

from __future__ import annotations

import argparse
import json
import os
import sys

import httpx

from streaming_client import ChatMessage, StreamingChatClient, print_stream


def _mask(secret: str) -> str:
    if len(secret) <= 8:
        return "***"
    return f"{secret[:3]}***{secret[-4:]}"


def demo_transport() -> httpx.MockTransport:
    """离线 Demo：返回一小段 SSE，模拟打字机效果。"""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        user_text = ""
        for m in body.get("messages") or []:
            if m.get("role") == "user":
                user_text = str(m.get("content") or "")
        reply = (
            f"[demo·stream] 收到：{user_text[:60]}"
            if user_text
            else "[demo·stream] （空提示）"
        )
        # 按字符拆成多个 delta，便于观察流式打印
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
    p = argparse.ArgumentParser(description="Day 13 · 流式终端聊天打印")
    p.add_argument(
        "-m",
        "--message",
        default="用一句话介绍什么是流式输出（SSE）",
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
    print("assistant  : ", end="", flush=True)
    with StreamingChatClient(
        base_url,
        api_key,
        model=model,
        transport=transport,
    ) as client:
        # print_stream 自己会再打一个换行；这里前缀已打印，避免重复 "assistant"
        text = print_stream(
            client.iter_content(messages, temperature=args.temperature)
        )

    print(f"chars      : {len(text)}")
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
