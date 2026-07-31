"""Day 7 手工运行入口：演示 503 后重试成功（Mock，无需外网）。"""

from __future__ import annotations

import httpx

from retry_client import HttpStatusError, RetryingJsonClient


def main() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if request.url.path == "/v1/unstable":
            if calls["n"] < 3:
                return httpx.Response(503, json={"error": "unavailable", "try": calls["n"]})
            return httpx.Response(200, json={"ok": True, "tries": calls["n"]})
        if request.url.path == "/v1/never":
            return httpx.Response(404, json={"error": "missing"})
        return httpx.Response(500, json={"error": "nope"})

    transport = httpx.MockTransport(handler)
    with RetryingJsonClient(
        "https://mock.local",
        max_retries=2,
        backoff_seconds=0.01,
        transport=transport,
    ) as client:
        print("unstable:", client.get_json("/v1/unstable"))
        print(f"(actual HTTP calls for unstable: {calls['n']})")
        try:
            client.get_json("/v1/never")
        except HttpStatusError as exc:
            print(f"expected non-retryable: HTTP {exc.status_code}")


if __name__ == "__main__":
    main()
