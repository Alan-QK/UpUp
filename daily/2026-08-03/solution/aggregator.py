"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Mapping

import httpx


@dataclass(frozen=True)
class SourceResult:
    name: str
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None


@dataclass(frozen=True)
class DailyBrief:
    city: str
    weather: SourceResult
    joke: SourceResult


async def _get_json(
    client: httpx.AsyncClient,
    name: str,
    path: str,
    *,
    params: Mapping[str, str] | None = None,
    headers: Mapping[str, str] | None = None,
) -> SourceResult:
    try:
        response = await client.get(path, params=params, headers=headers)
    except Exception as exc:
        return SourceResult(name=name, ok=False, error=type(exc).__name__)

    if response.status_code < 200 or response.status_code >= 300:
        return SourceResult(name=name, ok=False, error=f"HTTP {response.status_code}")

    try:
        data = response.json()
    except ValueError:
        return SourceResult(name=name, ok=False, error="invalid json")

    if not isinstance(data, dict):
        return SourceResult(name=name, ok=False, error="invalid payload")

    return SourceResult(name=name, ok=True, data=data)


async def fetch_weather(
    base_url: str,
    city: str,
    *,
    timeout: float = 5.0,
    transport: httpx.BaseTransport | None = None,
    api_key: str | None = None,
) -> SourceResult:
    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=timeout,
        transport=transport,
    ) as client:
        return await _get_json(
            client,
            "weather",
            "/weather",
            params={"city": city},
            headers=headers or None,
        )


async def fetch_joke(
    base_url: str,
    *,
    timeout: float = 5.0,
    transport: httpx.BaseTransport | None = None,
) -> SourceResult:
    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=timeout,
        transport=transport,
    ) as client:
        return await _get_json(client, "joke", "/joke")


async def build_daily_brief(
    city: str,
    *,
    weather_base_url: str,
    joke_base_url: str,
    timeout: float = 5.0,
    weather_transport: httpx.BaseTransport | None = None,
    joke_transport: httpx.BaseTransport | None = None,
    environ: Mapping[str, str] | None = None,
) -> DailyBrief:
    cleaned = city.strip()
    if not cleaned:
        raise ValueError("city must not be empty")

    env = environ if environ is not None else os.environ
    api_key = str(env.get("WEATHER_API_KEY", "")).strip() or None

    weather, joke = await asyncio.gather(
        fetch_weather(
            weather_base_url,
            cleaned,
            timeout=timeout,
            transport=weather_transport,
            api_key=api_key,
        ),
        fetch_joke(
            joke_base_url,
            timeout=timeout,
            transport=joke_transport,
        ),
    )
    return DailyBrief(city=cleaned, weather=weather, joke=joke)


def format_brief(brief: DailyBrief) -> str:
    lines = [f"=== 每日简报：{brief.city} ==="]

    if brief.weather.ok and brief.weather.data is not None:
        temp = brief.weather.data.get("temp_c", "?")
        condition = brief.weather.data.get("condition", "?")
        lines.append(f"天气：{temp}°C，{condition}")
    else:
        lines.append(f"天气：不可用（{brief.weather.error or 'unknown'}）")

    if brief.joke.ok and brief.joke.data is not None:
        setup = brief.joke.data.get("setup", "?")
        punchline = brief.joke.data.get("punchline", "?")
        lines.append(f"笑话：{setup} — {punchline}")
    else:
        lines.append(f"笑话：不可用（{brief.joke.error or 'unknown'}）")

    return "\n".join(lines) + "\n"


def demo_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/weather":
            city = request.url.params.get("city", "Unknown")
            return httpx.Response(
                200,
                json={"city": city, "temp_c": 28, "condition": "晴"},
            )
        if request.url.path == "/joke":
            return httpx.Response(
                200,
                json={
                    "setup": "为什么 Agent 喜欢 asyncio？",
                    "punchline": "因为工具一多，串行就不够用了。",
                },
            )
        return httpx.Response(404, json={"error": "not found"})

    return httpx.MockTransport(handler)
