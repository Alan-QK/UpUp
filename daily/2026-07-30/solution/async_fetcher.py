"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class FetchResult:
    path: str
    ok: bool
    data: Any | None = None
    error: str | None = None


async def fetch_one(client: httpx.AsyncClient, path: str) -> FetchResult:
    try:
        response = await client.get(path)
    except Exception as exc:
        return FetchResult(path=path, ok=False, error=type(exc).__name__)

    if response.status_code < 200 or response.status_code >= 300:
        return FetchResult(path=path, ok=False, error=f"HTTP {response.status_code}")

    try:
        data = response.json()
    except ValueError:
        return FetchResult(path=path, ok=False, error="invalid json")

    return FetchResult(path=path, ok=True, data=data)


async def fetch_many(
    base_url: str,
    paths: list[str],
    *,
    timeout: float = 5.0,
    transport: httpx.BaseTransport | None = None,
) -> list[FetchResult]:
    if not paths:
        return []

    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=timeout,
        transport=transport,
    ) as client:
        return list(await asyncio.gather(*(fetch_one(client, path) for path in paths)))
