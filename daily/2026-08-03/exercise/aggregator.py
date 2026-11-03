"""Day 10 练习：多 API 聚合（天气 + 笑话 → 每日简报）。

请完成 TODO，使 tests/ 全部通过。
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Mapping

import httpx


@dataclass(frozen=True)
class SourceResult:
    """单个数据源的结果。"""

    name: str
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None


@dataclass(frozen=True)
class DailyBrief:
    """聚合后的每日简报。"""

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
    """内部辅助：GET JSON，失败也返回 SourceResult（不向外抛）。

    规则与 Day 8 类似：
    - 2xx + 合法 JSON object → ok=True, data=dict
    - 2xx 但 JSON 不是 object → ok=False, error="invalid payload"
    - 非 2xx → ok=False, error="HTTP {code}"
    - JSON 解析失败 → ok=False, error="invalid json"
    - 其它异常 → ok=False, error=异常类名
    """
    # TODO: 实现这里
    raise NotImplementedError


async def fetch_weather(
    base_url: str,
    city: str,
    *,
    timeout: float = 5.0,
    transport: httpx.BaseTransport | None = None,
    api_key: str | None = None,
) -> SourceResult:
    """请求天气：GET {base_url}/weather?city=...

    - 成功时 SourceResult.name == "weather"，data 为响应 JSON
    - 若 api_key 非空，加 Header：Authorization: Bearer {api_key}
    - 失败同样返回 name="weather" 的 SourceResult
    """
    # TODO: 实现这里
    raise NotImplementedError


async def fetch_joke(
    base_url: str,
    *,
    timeout: float = 5.0,
    transport: httpx.BaseTransport | None = None,
) -> SourceResult:
    """请求笑话：GET {base_url}/joke

    成功/失败时 SourceResult.name 均为 "joke"。
    """
    # TODO: 实现这里
    raise NotImplementedError


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
    """并发拉取天气与笑话，聚合成 DailyBrief。

    要求：
    - 使用 asyncio.gather，而不是串行 await
    - api_key 从 environ（默认 os.environ）读取 WEATHER_API_KEY；空则传 None
    - city 先 strip；若为空 → ValueError("city must not be empty")
    """
    # TODO: 实现这里
    raise NotImplementedError


def format_brief(brief: DailyBrief) -> str:
    """把 DailyBrief 格式化成多行文本。

    约定格式（测试会检查关键片段）：

    === 每日简报：{city} ===
    天气：{temp_c}°C，{condition}
      或 天气：不可用（{error}）
    笑话：{setup} — {punchline}
      或 笑话：不可用（{error}）

    天气成功时从 data 取 temp_c / condition（缺字段用 "?"）。
    笑话成功时从 data 取 setup / punchline（缺字段用 "?"）。
    """
    # TODO: 实现这里
    raise NotImplementedError


def demo_transport() -> httpx.MockTransport:
    """离线 Demo / 测试可用的 Mock（两路 API）。

    - GET /weather?city=... → 固定晴天 JSON（city 回显 query）
    - GET /joke → 固定笑话 JSON
    - 其它 → 404
    """
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
