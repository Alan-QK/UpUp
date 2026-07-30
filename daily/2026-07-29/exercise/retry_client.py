"""Day 7 练习：带超时、重试与错误分类的 JSON HTTP 客户端。

请完成 TODO，使 tests/ 全部通过。
"""

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
    """判断 HTTP 状态码是否值得重试。

    规则：
    - 429 → True
    - 500–599 → True
    - 其余 → False（包括所有其他 4xx）
    """
    # TODO: 实现这里
    raise NotImplementedError


def is_retryable_exception(exc: BaseException) -> bool:
    """判断异常是否值得重试。

    规则：
    - httpx.TimeoutException → True
    - httpx.TransportError（含连接失败；注意 TimeoutException 也是其子类，已覆盖）→ True
    - HttpStatusError 且 is_retryable_status(exc.status_code) → True
    - 其他（含 HttpResponseError、普通 4xx 的 HttpStatusError）→ False
    """
    # TODO: 实现这里
    raise NotImplementedError


class RetryingJsonClient:
    """带有限次重试的 JSON 客户端。

    约定：
    - max_retries：额外重试次数。例如 max_retries=2 → 最多共 3 次请求
    - backoff_seconds：线性退避基数；第 attempt 次失败后 sleep = backoff * (attempt + 1)
      （attempt 从 0 起：第一次失败睡 1*backoff，第二次失败睡 2*backoff）
    - 单次请求使用 timeout
    - transport 可选，供测试注入 MockTransport
    - 支持 context manager
    """

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
        # TODO: 保存参数并创建 httpx.Client
        # 提示：把 sleep 存成 self._sleep，测试可注入假 sleep 避免真等
        raise NotImplementedError

    def close(self) -> None:
        # TODO: 关闭底层 Client
        raise NotImplementedError

    def __enter__(self) -> RetryingJsonClient:
        # TODO: 返回 self
        raise NotImplementedError

    def __exit__(self, *args: object) -> None:
        # TODO: close
        raise NotImplementedError

    def _parse_json(self, response: httpx.Response) -> Any:
        """状态非 2xx → HttpStatusError；JSON 解析失败 → HttpResponseError。"""
        # TODO: 实现这里（可参考 Day 6）
        raise NotImplementedError

    def _request_with_retry(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """发送请求；按分类决定是否重试。

        伪代码：
        last_exc = None
        for attempt in range(max_retries + 1):
            try:
                发 request → parse_json → return
            except Exception as exc:
                last_exc = exc
                if attempt >= max_retries or not is_retryable_exception(exc):
                    raise
                self._sleep(backoff_seconds * (attempt + 1))
        raise last_exc
        """
        # TODO: 实现这里
        raise NotImplementedError

    def get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        # TODO: 调用 _request_with_retry("GET", ...)
        raise NotImplementedError

    def post_json(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> Any:
        # TODO: 调用 _request_with_retry("POST", ...)
        raise NotImplementedError
