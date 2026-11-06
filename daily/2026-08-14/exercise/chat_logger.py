"""Day 19 练习：结构化日志（聊天 CLI 可观测雏形）。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, TextIO


Clock = Callable[[], datetime]


def utc_now() -> datetime:
    """默认时钟：aware UTC。"""
    return datetime.now(timezone.utc)


def should_mask_key(key: str) -> bool:
    """判断字段名是否需要脱敏。

    规则（大小写不敏感）：
    - 精确匹配：api_key / authorization / password / secret / token
    - 或以 _key / _secret / _token / _password 结尾
    """
    # TODO: 实现上述规则
    raise NotImplementedError


def mask_value(value: str, *, head: int = 3, tail: int = 4) -> str:
    """脱敏字符串。

    - 空串 → "***"
    - 长度 <= head + tail → "***"
    - 否则保留头 head、尾 tail，中间 "***"
    """
    # TODO: 实现脱敏
    raise NotImplementedError


def preview_text(text: str, *, limit: int = 40) -> str:
    """截断预览：strip 后超过 limit 则截断并加 ..."""
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit] + "..."


@dataclass
class StructuredLogger:
    """一行一条 JSON 的结构化日志器。"""

    sink: TextIO
    clock: Clock = utc_now
    secret_keys: frozenset[str] | None = None
    # 若提供 secret_keys，则「精确匹配（小写）」也会触发脱敏（额外名单）
    # 启发式 should_mask_key 始终生效

    def log(
        self,
        level: str,
        event: str,
        *,
        ts: datetime | None = None,
        **fields: Any,
    ) -> None:
        """写一条日志。

        输出对象必须包含：
        - ts: (ts 或 clock()) 的 ISO 格式（datetime.isoformat()）
        - level: 原样写入（调用方负责传 debug/info/warning/error）
        - event: 事件名

        其余 fields：
        - 若值是 str 且 should_mask_key(字段名) 或字段名小写在 secret_keys 中 → mask_value
        - 其他 JSON 可序列化值原样写入
        - 写入后必须换行（一条一行）
        """
        # TODO: 组装 payload，json.dumps 后写入 sink
        raise NotImplementedError

    def log_chat_turn(
        self,
        *,
        session_id: str,
        model: str,
        user_text: str,
        complete: Callable[[], str],
    ) -> str:
        """记录一轮聊天：先 request，再调用 complete()。

        成功：
        - chat.request（含 session_id/model/user_preview/user_chars）
        - chat.response（含 session_id/model/latency_ms/reply_preview/reply_chars）
        - 返回 complete() 的结果

        失败（complete 抛任何异常）：
        - 已写过 chat.request
        - 再写 chat.error（session_id/model/error_type/error_message）
        - 然后原样向上抛出异常

        时钟约定（便于单测注入）：
        1. clock() → 作为 chat.request 的 ts
        2. clock() → latency 起点（在调用 complete 之前）
        3. 成功：clock() → latency 终点，并作为 chat.response 的 ts
           失败：chat.error 的 ts 由 log() 内部再 clock() 一次

        latency_ms： (终点 - 起点).total_seconds() * 1000，四舍五入为 int。
        user_preview / reply_preview：用 preview_text。
        user_chars：strip 后的字符数。
        error_message：str(exc)，若超过 120 字符则截断加 ...
        error_type：type(exc).__name__
        """
        # TODO: 实现 request / response / error 闭环
        raise NotImplementedError


def sanitize_fields(
    fields: Mapping[str, Any],
    *,
    extra_secret_keys: frozenset[str] | None = None,
) -> dict[str, Any]:
    """对 mapping 做一份脱敏拷贝（供 log 复用，也可单测）。"""
    # TODO: 实现；字符串且需脱敏时替换为 mask_value(value)
    raise NotImplementedError
