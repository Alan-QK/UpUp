"""Day 8 练习：asyncio 并发拉取多个 JSON 接口。

请完成 TODO，使 tests/ 全部通过。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class FetchResult:
    """单次请求的汇总结果。

    Attributes:
        path: 请求路径（与入参一致）
        ok: 是否成功拿到 JSON
        data: 成功时的 JSON；失败时为 None
        error: 失败时的简短原因；成功时为 None
    """

    path: str
    ok: bool
    data: Any | None = None
    error: str | None = None


async def fetch_one(client: httpx.AsyncClient, path: str) -> FetchResult:
    """用已有 AsyncClient GET 一个 path，返回 FetchResult。

    规则：
    - status 在 200–299：ok=True，data=response.json()
    - status 非 2xx：ok=False，error 形如 "HTTP 404"
    - JSON 解析失败：ok=False，error="invalid json"
    - 其它异常（超时、连接失败等）：ok=False，error=异常类名或短消息
    - 本函数**不应向外抛异常**（失败也要变成 FetchResult）
    """
    # TODO: 实现这里
    raise NotImplementedError


async def fetch_many(
    base_url: str,
    paths: list[str],
    *,
    timeout: float = 5.0,
    transport: httpx.BaseTransport | None = None,
) -> list[FetchResult]:
    """并发请求多个 path，返回与 paths **同序** 的结果列表。

    要求：
    - 使用 httpx.AsyncClient（支持 base_url / timeout / transport）
    - 使用 asyncio.gather 并发，而不是 for 里顺序 await
    - 单个失败不影响其它（依赖 fetch_one 吞掉异常）
    - 空 paths → 返回 []
    """
    # TODO: 实现这里
    raise NotImplementedError
