"""Day 10 手工运行入口：每日简报 CLI。"""

from __future__ import annotations

import argparse
import asyncio
import sys

from aggregator import build_daily_brief, demo_transport, format_brief

DEFAULT_WEATHER_URL = "https://weather.test"
DEFAULT_JOKE_URL = "https://joke.test"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="brief", description="多 API 聚合 CLI（Day 10）")
    sub = parser.add_subparsers(dest="command", required=True)

    brief_p = sub.add_parser("brief", help="拉取天气+笑话并打印摘要")
    brief_p.add_argument("city", help="城市名，例如 Shanghai")
    brief_p.add_argument(
        "--demo",
        action="store_true",
        help="使用内置 MockTransport（无需外网）",
    )
    brief_p.add_argument("--weather-url", default=DEFAULT_WEATHER_URL)
    brief_p.add_argument("--joke-url", default=DEFAULT_JOKE_URL)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command != "brief":
        return 1

    transport = demo_transport() if args.demo else None

    try:
        brief = asyncio.run(
            build_daily_brief(
                args.city,
                weather_base_url=args.weather_url,
                joke_base_url=args.joke_url,
                weather_transport=transport,
                joke_transport=transport,
            )
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(format_brief(brief), end="")
    # 两个源都失败时返回非 0，方便脚本判断
    if not brief.weather.ok and not brief.joke.ok:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
