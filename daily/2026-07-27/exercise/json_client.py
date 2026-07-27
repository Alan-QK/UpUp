"""Day 6 练习：封装 GET/POST JSON 的 httpx 客户端。

请完成 TODO，使 tests/ 全部通过。
"""

from __future__ import annotations

from typing import Any

import httpx


class HttpStatusError(Exception):
    """HTTP 状态码不在 2xx。

    Attributes:
        status_code: 响应状态码
        body: 响应文本（便于调试；可能为空）
    """

    def __init__(self, status_code: int, body: str = "") -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {body[:200]}")


class HttpResponseError(Exception):
    """响应无法按 JSON 解析。"""


class JsonClient:
    """面向 JSON API 的薄封装。

    约定：
    - path 以 / 开头，拼到 base_url 后面（与 httpx.Client 一致）
    - 默认 timeout（秒）
    - 支持 context manager：with JsonClient(...) as c:
    - transport 可选，测试时传入 httpx.MockTransport
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 10.0,
        headers: dict[str, str] | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        # TODO: 保存参数，并创建 httpx.Client
        # 提示：httpx.Client(base_url=..., timeout=..., headers=..., transport=...)
        raise NotImplementedError

    def close(self) -> None:
        """关闭底层 Client。"""
        # TODO: 实现这里
        raise NotImplementedError

    def __enter__(self) -> JsonClient:
        # TODO: 返回 self
        raise NotImplementedError

    def __exit__(self, *args: object) -> None:
        # TODO: 调用 close()
        raise NotImplementedError

    def get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """GET 并返回解析后的 JSON。

        规则：
        - status 不在 200–299 → HttpStatusError(status_code, response.text)
        - status OK 但 JSON 解析失败 → HttpResponseError
        """
        # TODO: 实现这里
        raise NotImplementedError

    def post_json(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """POST JSON body，并返回解析后的 JSON。

        规则同 get_json。请求体用 httpx 的 json= 参数。
        """
        # TODO: 实现这里
        raise NotImplementedError
