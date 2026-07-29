"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import time
from typing import Any, Callable

import httpx


class HttpStatusError(Exception):
    """HTTP 状态码不在 2xx。"""

    def __init__(self, status_code: int, body: str = "") -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {body[:200]}")


class HttpResponseError(Exception):
    """响应无法按 JSON 解析。"""


def is_retryable_status(status_code: int) -> bool:
    if status_code == 429:
        return True
    return 500 <= status_code <= 599


def is_retryable_exception(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, HttpStatusError):
        return is_retryable_status(exc.status_code)
    return False


class RetryingJsonClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 5.0,
        max_retries: int = 2,
        backoff_seconds: float = 0.05,
        headers: dict[str, str] | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds
        self._sleep = sleep
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> RetryingJsonClient:
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

    def _request_with_retry(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        last_exc: BaseException | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.request(
                    method,
                    path,
                    params=params,
                    json=json,
                )
                return self._parse_json(response)
            except Exception as exc:
                last_exc = exc
                if attempt >= self._max_retries or not is_retryable_exception(exc):
                    raise
                self._sleep(self._backoff_seconds * (attempt + 1))
        assert last_exc is not None
        raise last_exc

    def get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return self._request_with_retry("GET", path, params=params)

    def post_json(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> Any:
        return self._request_with_retry("POST", path, json=json)
