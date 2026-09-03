"""Day 17 手工运行入口：对比不同 temperature 的输出并打印报告。"""

from __future__ import annotations

import argparse
import json
import os
import sys

import httpx

from chat_client import ChatClient, ChatMessage
from sampling_lab import format_comparison_report, run_temperature_sweep

DEFAULT_PROMPT = (
    "用不超过两句话，给「上下文窗口」打一个有画面感的比方。"
    "可以俏皮，但必须让前端工程师听得懂。"
)


def _mask(secret: str) -> str:
    if len(secret) <= 8:
        return "***"
    return f"{secret[:3]}***{secret[-4:]}"


def _parse_floats(raw: str) -> list[float]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return [float(p) for p in parts]


def demo_transport() -> httpx.MockTransport:
    """离线 Demo：按 temperature 返回风格差异明显的固定文案。"""

    canned: dict[float, str] = {
        0.0: (
            "上下文窗口就像浏览器只保留最近几个标签页："
            "超出的旧标签会被关掉，模型也记不住更早的内容。"
        ),
        0.7: (
            "你可以把它想成手机通知栏：新消息往上堆，"
            "滑太远的旧通知就被挤走；Agent 也只能看见还留在栏里的对话。"
        ),
        1.5: (
            "想象一辆只会往后看三面后视镜的星际巴士——"
            "再远的星尘再浪漫，后视镜里也没有，模型照样装作没见过。"
        ),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        temp = body.get("temperature")
        try:
            key = float(temp)
        except (TypeError, ValueError):
            key = 0.7
        # 找不到精确键时，挑一个「最接近」的 canned
        if key not in canned:
            key = min(canned.keys(), key=lambda k: abs(k - key))
        reply = canned[key]
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
                    "prompt_tokens": 20,
                    "completion_tokens": max(1, len(reply) // 4),
                    "total_tokens": 20 + max(1, len(reply) // 4),
                },
            },
        )

    return httpx.MockTransport(handler)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Day 17 · temperature 采样对比")
    p.add_argument(
        "-p",
        "--prompt",
        default=DEFAULT_PROMPT,
        help="发给模型的用户提示",
    )
    p.add_argument(
        "-t",
        "--temperatures",
        default="0.0,0.7,1.5",
        help="逗号分隔的 temperature 列表（默认 0.0,0.7,1.5）",
    )
    p.add_argument(
        "--top-p",
        type=float,
        default=None,
        help="可选 top_p；省略则不传给 API",
    )
    p.add_argument(
        "--system",
        default="你是简洁、略带幽默的技术助教。用中文回答。",
        help="system 提示",
    )
    p.add_argument(
        "--demo",
        action="store_true",
        help="使用 MockTransport，不访问外网",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        temperatures = _parse_floats(args.temperatures)
    except ValueError:
        print("无法解析 --temperatures，请用逗号分隔数字", file=sys.stderr)
        return 2

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

    print(f"temperatures: {temperatures}")
    print(f"top_p       : {args.top_p if args.top_p is not None else 'default'}")
    print(f"prompt      : {args.prompt[:80]}...")
    print("---")

    messages = [
        ChatMessage("system", args.system),
        ChatMessage("user", args.prompt),
    ]

    with ChatClient(
        base_url,
        api_key,
        model=model,
        transport=transport,
    ) as client:
        runs = run_temperature_sweep(
            client,
            messages,
            temperatures,
            top_p=args.top_p,
        )
        print(format_comparison_report(runs), end="")

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
