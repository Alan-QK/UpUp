"""Day 14 手工运行入口：用量估算与费用日志演示。"""

from __future__ import annotations

import argparse
import json
import os
import sys

from usage_meter import DEFAULT_PRICING, ModelPricing, UsageLedger, join_message_contents


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Day 14 · Token / 成本账本 Demo")
    p.add_argument(
        "--demo",
        action="store_true",
        help="离线演示：估算 + 模拟 API usage 记账",
    )
    p.add_argument(
        "--with-chat",
        action="store_true",
        help="额外发起一次 Chat Completions（需 httpx；与 --demo 联用时走 Mock）",
    )
    p.add_argument(
        "-m",
        "--message",
        default="用一句话解释什么是 token",
        help="--with-chat 时的用户消息",
    )
    return p


def _pricing_for(model: str) -> ModelPricing:
    if model in DEFAULT_PRICING:
        return DEFAULT_PRICING[model]
    # 未知模型：沿用 gpt-4o-mini 示意单价，仅改 model 名
    base = DEFAULT_PRICING["gpt-4o-mini"]
    return ModelPricing(model, base.input_usd_per_1m, base.output_usd_per_1m)


def run_offline_ledger(ledger: UsageLedger) -> None:
    pricing = DEFAULT_PRICING["gpt-4o-mini"]

    r1 = ledger.record_from_texts(
        model="gpt-4o-mini",
        prompt_text="你是简洁助手。\n什么是 token？",
        completion_text="Token 是模型计费与上下文的基本单位。",
        pricing=pricing,
    )
    print(ledger.format_log_line(r1))

    r2 = ledger.record_from_api_usage(
        model="gpt-4o-mini",
        prompt_tokens=120,
        completion_tokens=45,
        pricing=pricing,
        prompt_text="（有 API usage 时文本仅作兜底，不会用到）",
        completion_text="ignored",
    )
    print(ledger.format_log_line(r2))

    r3 = ledger.record_from_api_usage(
        model="gpt-4o-mini",
        prompt_tokens=None,
        completion_tokens=None,
        pricing=pricing,
        prompt_text="缺少 usage 时的 prompt",
        completion_text="缺少 usage 时的回复",
    )
    print(ledger.format_log_line(r3))


def run_with_chat(ledger: UsageLedger, *, demo: bool, message: str) -> None:
    try:
        import httpx
    except ImportError:
        print("需要 httpx：python3 -m pip install --user httpx", file=sys.stderr)
        raise SystemExit(2) from None

    from chat_client import ChatClient, ChatMessage

    if demo:

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode("utf-8") or "{}")
            return httpx.Response(
                200,
                json={
                    "id": "chatcmpl-demo",
                    "model": body.get("model") or "demo-model",
                    "choices": [
                        {
                            "index": 0,
                            "finish_reason": "stop",
                            "message": {
                                "role": "assistant",
                                "content": "[demo] token 是计费单位。",
                            },
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 18,
                        "completion_tokens": 9,
                        "total_tokens": 27,
                    },
                },
            )

        base_url = "https://api.test/v1"
        api_key = "sk-demo"
        model = "demo-model"
        transport = httpx.MockTransport(handler)
        print("chat mode  : demo MockTransport")
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        base_url = os.environ.get(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        ).strip()
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()
        if not api_key:
            print(
                "缺少 OPENAI_API_KEY。可先：python3 main.py --demo --with-chat",
                file=sys.stderr,
            )
            raise SystemExit(2)
        transport = None
        print("chat mode  : live")

    pricing = _pricing_for(model)
    messages = [
        ChatMessage(role="system", content="你是简洁的中文助手。"),
        ChatMessage(role="user", content=message),
    ]
    with ChatClient(
        base_url, api_key, model=model, transport=transport
    ) as client:
        result = client.complete(messages)

    rec = ledger.record_from_api_usage(
        model=result.model or model,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        pricing=pricing,
        prompt_text=join_message_contents(messages),
        completion_text=result.content,
    )
    print(f"assistant  : {result.content}")
    print(ledger.format_log_line(rec))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.demo and not args.with_chat:
        print("请指定 --demo 和/或 --with-chat", file=sys.stderr)
        return 2

    ledger = UsageLedger()

    if args.demo:
        run_offline_ledger(ledger)
        if args.with_chat:
            print("---")
            run_with_chat(ledger, demo=True, message=args.message)
    else:
        run_with_chat(ledger, demo=False, message=args.message)

    print("---")
    print(ledger.format_summary())
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
