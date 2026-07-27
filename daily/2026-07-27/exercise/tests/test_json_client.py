"""Day 6：JsonClient 测试（全部离线 Mock）。"""

from __future__ import annotations

import json

import httpx
import pytest

from json_client import HttpResponseError, HttpStatusError, JsonClient


def _handler(request: httpx.Request) -> httpx.Response:
    if request.method == "GET" and request.url.path == "/items":
        q = request.url.params.get("q", "")
        return httpx.Response(200, json={"items": [q], "method": "GET"})

    if request.method == "POST" and request.url.path == "/items":
        body = json.loads(request.content.decode("utf-8") or "{}")
        return httpx.Response(201, json={"created": body})

    if request.url.path == "/plain":
        return httpx.Response(200, text="not-json", headers={"content-type": "text/plain"})

    if request.url.path == "/gone":
        return httpx.Response(404, json={"error": "missing"})

    return httpx.Response(500, json={"error": "nope"})


@pytest.fixture
def client() -> JsonClient:
    transport = httpx.MockTransport(_handler)
    with JsonClient("https://api.test", timeout=5.0, transport=transport) as c:
        yield c


def test_get_json_with_params(client: JsonClient) -> None:
    data = client.get_json("/items", params={"q": "agent"})
    assert data == {"items": ["agent"], "method": "GET"}


def test_post_json(client: JsonClient) -> None:
    data = client.post_json("/items", json={"name": "tool"})
    assert data == {"created": {"name": "tool"}}


def test_status_error(client: JsonClient) -> None:
    with pytest.raises(HttpStatusError) as ei:
        client.get_json("/gone")
    assert ei.value.status_code == 404
    assert "missing" in ei.value.body


def test_invalid_json_raises(client: JsonClient) -> None:
    with pytest.raises(HttpResponseError):
        client.get_json("/plain")


def test_context_manager_closes() -> None:
    transport = httpx.MockTransport(_handler)
    client = JsonClient("https://api.test", transport=transport)
    with client:
        assert client.get_json("/items", params={"q": "x"})["items"] == ["x"]
    # 关闭后再请求应失败（底层 client 已 close）
    with pytest.raises(RuntimeError):
        client.get_json("/items", params={"q": "y"})
