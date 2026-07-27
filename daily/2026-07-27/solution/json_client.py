"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

from typing import Any

import httpx


class HttpStatusError(Exception):
    """HTTP 状态码不在 2xx。"""

    def __init__(self, status_code: int, body: str = "") -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {body[:200]}")


class HttpResponseError(Exception):
    """响应无法按 JSON 解析。"""


class JsonClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 10.0,
        headers: dict[str, str] | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> JsonClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _parse_json(self, response: httpx.Response) -> Any:
        if response.status_code < 200 or response.status_code >= 300:
            raise HttpStatusError(response.status_code, response.text)
        try:
            return response.json()
        except ValueError as exc:
            raise HttpResponseError(str(exc)) from exc

    def get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        response = self._client.get(path, params=params)
        return self._parse_json(response)

    def post_json(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> Any:
        response = self._client.post(path, json=json)
        return self._parse_json(response)
