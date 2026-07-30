"""Day 8：async_fetcher 测试（全部离线 Mock）。"""

from __future__ import annotations

import asyncio

import httpx

from async_fetcher import FetchResult, fetch_many, fetch_one


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/a":
        return httpx.Response(200, json={"id": "a"})
    if path == "/b":
        return httpx.Response(200, json={"id": "b"})
    if path == "/c":
        return httpx.Response(200, json={"id": "c"})
    if path == "/gone":
        return httpx.Response(404, json={"error": "missing"})
    if path == "/plain":
        return httpx.Response(200, text="not-json", headers={"content-type": "text/plain"})
    if path == "/boom":
        raise httpx.ReadTimeout("slow")
    return httpx.Response(500, json={"error": "nope"})


def test_fetch_one_ok() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(_handler)
        async with httpx.AsyncClient(
            base_url="https://api.test",
            transport=transport,
            timeout=2.0,
        ) as client:
            result = await fetch_one(client, "/a")
        assert result == FetchResult(path="/a", ok=True, data={"id": "a"}, error=None)

    asyncio.run(run())


def test_fetch_one_http_error() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(_handler)
        async with httpx.AsyncClient(
            base_url="https://api.test",
            transport=transport,
        ) as client:
            result = await fetch_one(client, "/gone")
        assert result.ok is False
        assert result.data is None
        assert result.error == "HTTP 404"

    asyncio.run(run())


def test_fetch_one_invalid_json() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(_handler)
        async with httpx.AsyncClient(
            base_url="https://api.test",
            transport=transport,
        ) as client:
            result = await fetch_one(client, "/plain")
        assert result.ok is False
        assert result.error == "invalid json"

    asyncio.run(run())


def test_fetch_one_timeout() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(_handler)
        async with httpx.AsyncClient(
            base_url="https://api.test",
            transport=transport,
        ) as client:
            result = await fetch_one(client, "/boom")
        assert result.ok is False
        assert result.error is not None
        assert "Timeout" in result.error or "slow" in result.error

    asyncio.run(run())


def test_fetch_many_preserves_order_and_isolates_errors() -> None:
    async def run() -> None:
        results = await fetch_many(
            "https://api.test",
            ["/a", "/gone", "/b"],
            transport=httpx.MockTransport(_handler),
        )
        assert [r.path for r in results] == ["/a", "/gone", "/b"]
        assert results[0].ok is True and results[0].data == {"id": "a"}
        assert results[1].ok is False and results[1].error == "HTTP 404"
        assert results[2].ok is True and results[2].data == {"id": "b"}

    asyncio.run(run())


def test_fetch_many_empty() -> None:
    async def run() -> None:
        results = await fetch_many(
            "https://api.test",
            [],
            transport=httpx.MockTransport(_handler),
        )
        assert results == []

    asyncio.run(run())


def test_fetch_many_three_urls() -> None:
    calls = {"n": 0}

    def counting_handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"path": request.url.path})

    async def run() -> None:
        results = await fetch_many(
            "https://api.test",
            ["/a", "/b", "/c"],
            transport=httpx.MockTransport(counting_handler),
        )
        assert calls["n"] == 3
        assert len(results) == 3
        assert all(r.ok for r in results)
        assert [r.data["path"] for r in results] == ["/a", "/b", "/c"]

    asyncio.run(run())
