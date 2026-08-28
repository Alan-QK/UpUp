"""Day 10：多 API 聚合测试（全部离线 Mock）。"""

from __future__ import annotations

import asyncio

import httpx
import pytest

from aggregator import (
    DailyBrief,
    SourceResult,
    build_daily_brief,
    demo_transport,
    fetch_joke,
    fetch_weather,
    format_brief,
)


def _weather_ok(request: httpx.Request) -> httpx.Response:
    city = request.url.params.get("city", "")
    return httpx.Response(
        200,
        json={"city": city, "temp_c": 26, "condition": "多云"},
    )


def _joke_ok(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={"setup": "Q", "punchline": "A"},
    )


def test_fetch_weather_ok() -> None:
    async def run() -> None:
        result = await fetch_weather(
            "https://weather.test",
            "Shanghai",
            transport=httpx.MockTransport(_weather_ok),
        )
        assert result == SourceResult(
            name="weather",
            ok=True,
            data={"city": "Shanghai", "temp_c": 26, "condition": "多云"},
        )

    asyncio.run(run())


def test_fetch_weather_sends_bearer_when_key() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers.get("Authorization", "")
        return _weather_ok(request)

    async def run() -> None:
        result = await fetch_weather(
            "https://weather.test",
            "Paris",
            transport=httpx.MockTransport(handler),
            api_key="secret-key",
        )
        assert result.ok is True
        assert seen["authorization"] == "Bearer secret-key"

    asyncio.run(run())


def test_fetch_joke_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "busy"})

    async def run() -> None:
        result = await fetch_joke(
            "https://joke.test",
            transport=httpx.MockTransport(handler),
        )
        assert result.name == "joke"
        assert result.ok is False
        assert result.error == "HTTP 503"

    asyncio.run(run())


def test_build_daily_brief_concurrent_and_partial_failure() -> None:
    calls = {"weather": 0, "joke": 0}

    def weather_handler(request: httpx.Request) -> httpx.Response:
        calls["weather"] += 1
        return _weather_ok(request)

    def joke_handler(request: httpx.Request) -> httpx.Response:
        calls["joke"] += 1
        return httpx.Response(500, json={"error": "nope"})

    async def run() -> None:
        brief = await build_daily_brief(
            "  Shanghai  ",
            weather_base_url="https://weather.test",
            joke_base_url="https://joke.test",
            weather_transport=httpx.MockTransport(weather_handler),
            joke_transport=httpx.MockTransport(joke_handler),
            environ={},
        )
        assert isinstance(brief, DailyBrief)
        assert brief.city == "Shanghai"
        assert brief.weather.ok is True
        assert brief.joke.ok is False
        assert brief.joke.error == "HTTP 500"
        assert calls["weather"] == 1 and calls["joke"] == 1

    asyncio.run(run())


def test_build_daily_brief_reads_api_key_from_environ() -> None:
    seen: dict[str, str] = {}

    def weather_handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers.get("Authorization", "")
        return _weather_ok(request)

    async def run() -> None:
        await build_daily_brief(
            "Berlin",
            weather_base_url="https://weather.test",
            joke_base_url="https://joke.test",
            weather_transport=httpx.MockTransport(weather_handler),
            joke_transport=httpx.MockTransport(_joke_ok),
            environ={"WEATHER_API_KEY": "from-env"},
        )
        assert seen["authorization"] == "Bearer from-env"

    asyncio.run(run())


def test_build_daily_brief_empty_city() -> None:
    async def run() -> None:
        with pytest.raises(ValueError, match="city must not be empty"):
            await build_daily_brief(
                "   ",
                weather_base_url="https://weather.test",
                joke_base_url="https://joke.test",
                weather_transport=demo_transport(),
                joke_transport=demo_transport(),
            )

    asyncio.run(run())


def test_format_brief_success_and_failure() -> None:
    ok = DailyBrief(
        city="Shanghai",
        weather=SourceResult(
            name="weather",
            ok=True,
            data={"temp_c": 28, "condition": "晴"},
        ),
        joke=SourceResult(name="joke", ok=False, error="HTTP 404"),
    )
    text = format_brief(ok)
    assert "每日简报：Shanghai" in text
    assert "天气：28°C，晴" in text
    assert "笑话：不可用（HTTP 404）" in text

    both_ok = DailyBrief(
        city="Tokyo",
        weather=SourceResult(
            name="weather",
            ok=True,
            data={"temp_c": 20, "condition": "雨"},
        ),
        joke=SourceResult(
            name="joke",
            ok=True,
            data={"setup": "Hi", "punchline": "Ho"},
        ),
    )
    text2 = format_brief(both_ok)
    assert "笑话：Hi — Ho" in text2


def test_demo_transport_roundtrip() -> None:
    async def run() -> None:
        transport = demo_transport()
        brief = await build_daily_brief(
            "Shanghai",
            weather_base_url="https://weather.test",
            joke_base_url="https://joke.test",
            weather_transport=transport,
            joke_transport=transport,
            environ={},
        )
        assert brief.weather.ok and brief.joke.ok
        assert brief.weather.data is not None
        assert brief.weather.data["city"] == "Shanghai"
        assert "asyncio" in format_brief(brief)

    asyncio.run(run())
