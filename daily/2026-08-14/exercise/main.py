"""Day 19 手工运行入口：观察结构化日志。"""

from __future__ import annotations

import argparse
import sys
import time

from chat_logger import StructuredLogger


class BoomError(RuntimeError):
    """Demo 用的故意失败。"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Day 19 · 结构化日志 Demo")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="离线演示一轮成功聊天日志（可与 --fail 组合）",
    )
    parser.add_argument(
        "--fail",
        action="store_true",
        help="故意让 complete 抛错，观察 chat.error",
    )
    parser.add_argument(
        "--message",
        "-m",
        default="一句话解释什么是结构化日志？",
        help="模拟用户输入",
    )
    parser.add_argument(
        "--api-key",
        default="sk-demo-super-secret-key-123456",
        help="演示脱敏用的假密钥（不会发网）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.demo and not args.fail:
        # 默认走 demo
        args.demo = True

    sink = sys.stdout
    logger = StructuredLogger(sink=sink)

    logger.log(
        "info",
        "cli.start",
        session_id="demo-session",
        api_key=args.api_key,
        mode="fail" if args.fail else "ok",
    )

    def complete_ok() -> str:
        # 轻微延迟，让 latency_ms > 0（真实 clock）
        time.sleep(0.01)
        return f"结构化日志 = 一行一条可机读事件。你问的是：{args.message[:20]}"

    def complete_fail() -> str:
        time.sleep(0.01)
        raise BoomError("provider timeout (demo)")

    complete = complete_fail if args.fail else complete_ok

    try:
        reply = logger.log_chat_turn(
            session_id="demo-session",
            model="fake-demo",
            user_text=args.message,
            complete=complete,
        )
    except BoomError as exc:
        print(f"[user-facing] 调用失败：{exc}", file=sys.stderr)
        logger.log("info", "cli.end", session_id="demo-session", ok=False)
        return 1

    print(f"[assistant] {reply}")
    logger.log("info", "cli.end", session_id="demo-session", ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
