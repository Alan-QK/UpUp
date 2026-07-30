"""Day 8 手工运行入口：Mock 并发拉取 3 个接口（无需外网）。"""

from __future__ import annotations

import asyncio
import time

import httpx

from async_fetcher import fetch_many


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/v1/weather":
        return httpx.Response(200, json={"city": "Shanghai", "temp_c": 28})
    if path == "/v1/news":
        return httpx.Response(200, json={"headlines": ["Agent ships", "Async wins"]})
    if path == "/v1/missing":
        return httpx.Response(404, json={"error": "not found"})
    return httpx.Response(500, json={"error": "nope"})


async def _run() -> None:
    transport = httpx.MockTransport(_handler)
    paths = ["/v1/weather", "/v1/news", "/v1/missing"]
    started = time.perf_counter()
    results = await fetch_many(
        "https://mock.local",
        paths,
        timeout=2.0,
        transport=transport,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    for item in results:
        print(f"{item.path}: ok={item.ok} data={item.data} error={item.error}")
    print(f"elapsed ≈ {elapsed_ms:.1f} ms（Mock 几乎瞬时；真实网络时会接近最慢一路）")


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
