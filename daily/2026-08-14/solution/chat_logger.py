"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, TextIO


Clock = Callable[[], datetime]

_EXACT_SECRET_NAMES = frozenset(
    {"api_key", "authorization", "password", "secret", "token"}
)
_SECRET_SUFFIXES = ("_key", "_secret", "_token", "_password")


def utc_now() -> datetime:
    """默认时钟：aware UTC。"""
    return datetime.now(timezone.utc)


def should_mask_key(key: str) -> bool:
    """判断字段名是否需要脱敏。"""
    lowered = key.lower()
    if lowered in _EXACT_SECRET_NAMES:
        return True
    return any(lowered.endswith(suffix) for suffix in _SECRET_SUFFIXES)


def mask_value(value: str, *, head: int = 3, tail: int = 4) -> str:
    """脱敏字符串。"""
    if not value or len(value) <= head + tail:
        return "***"
    return f"{value[:head]}***{value[-tail:]}"


def preview_text(text: str, *, limit: int = 40) -> str:
    """截断预览：strip 后超过 limit 则截断并加 ..."""
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit] + "..."


def sanitize_fields(
    fields: Mapping[str, Any],
    *,
    extra_secret_keys: frozenset[str] | None = None,
) -> dict[str, Any]:
    """对 mapping 做一份脱敏拷贝。"""
    extra = {k.lower() for k in (extra_secret_keys or frozenset())}
    out: dict[str, Any] = {}
    for key, value in fields.items():
        if isinstance(value, str) and (
            should_mask_key(key) or key.lower() in extra
        ):
            out[key] = mask_value(value)
        else:
            out[key] = value
    return out


@dataclass
class StructuredLogger:
    """一行一条 JSON 的结构化日志器。"""

    sink: TextIO
    clock: Clock = utc_now
    secret_keys: frozenset[str] | None = None

    def log(
        self,
        level: str,
        event: str,
        *,
        ts: datetime | None = None,
        **fields: Any,
    ) -> None:
        """写一条日志。"""
        when = ts if ts is not None else self.clock()
        payload: dict[str, Any] = {
            "ts": when.isoformat(),
            "level": level,
            "event": event,
        }
        payload.update(
            sanitize_fields(fields, extra_secret_keys=self.secret_keys)
        )
        self.sink.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def log_chat_turn(
        self,
        *,
        session_id: str,
        model: str,
        user_text: str,
        complete: Callable[[], str],
    ) -> str:
        """记录一轮聊天：request → complete → response / error。"""
        request_ts = self.clock()
        stripped = user_text.strip()
        self.log(
            "info",
            "chat.request",
            ts=request_ts,
            session_id=session_id,
            model=model,
            user_preview=preview_text(user_text),
            user_chars=len(stripped),
        )

        started_at = self.clock()
        try:
            reply = complete()
        except Exception as exc:
            message = str(exc)
            if len(message) > 120:
                message = message[:120] + "..."
            self.log(
                "error",
                "chat.error",
                session_id=session_id,
                model=model,
                error_type=type(exc).__name__,
                error_message=message,
            )
            raise

        ended_at = self.clock()
        latency_ms = int(round((ended_at - started_at).total_seconds() * 1000))
        self.log(
            "info",
            "chat.response",
            ts=ended_at,
            session_id=session_id,
            model=model,
            latency_ms=latency_ms,
            reply_preview=preview_text(reply),
            reply_chars=len(reply),
        )
        return reply
