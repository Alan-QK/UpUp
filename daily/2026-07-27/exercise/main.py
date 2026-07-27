"""Day 6 手工运行入口：用 MockTransport 演示 JsonClient（无需外网）。"""

from __future__ import annotations

import json

import httpx

from json_client import HttpStatusError, JsonClient


def _mock_handler(request: httpx.Request) -> httpx.Response:
    """伪造一个极简 echo API。"""
    if request.method == "GET" and request.url.path == "/v1/ping":
        return httpx.Response(200, json={"ok": True, "service": "mock-agent"})

    if request.method == "POST" and request.url.path == "/v1/echo":
        payload = json.loads(request.content.decode("utf-8") or "{}")
        return httpx.Response(200, json={"echo": payload})

    if request.url.path == "/v1/boom":
        return httpx.Response(503, json={"error": "unavailable"})

    return httpx.Response(404, json={"error": "not found"})


def main() -> None:
    transport = httpx.MockTransport(_mock_handler)
    with JsonClient("https://mock.local", transport=transport) as client:
        print("ping:", client.get_json("/v1/ping"))
        print("echo:", client.post_json("/v1/echo", json={"msg": "hello agent"}))
        try:
            client.get_json("/v1/boom")
        except HttpStatusError as exc:
            print(f"expected error: HTTP {exc.status_code}")


if __name__ == "__main__":
    main()
