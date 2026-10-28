"""Day 13 练习：OpenAI 兼容 Chat Completions（流式）客户端。

请完成 TODO，使 tests/ 全部通过。
构造器与上下文管理已给齐；重点在 SSE 解析与流式读取。
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Any, Sequence, TextIO

import httpx


class ChatClientError(Exception):
    """Chat 客户端相关错误的基类。"""


class ChatHttpError(ChatClientError):
    """HTTP 状态码不在 2xx。"""

    def __init__(self, status_code: int, body: str = "") -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {body[:200]}")


class ChatResponseError(ChatClientError):
    """流式响应无法按约定协议解析。"""


@dataclass(frozen=True)
class ChatMessage:
    """一条对话消息。"""

    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


def parse_sse_data_line(line: str) -> str | None:
    """从一行 SSE 文本中提取 data payload。

    规则：
    - 去掉行尾 ``\\r`` 后判断
    - 必须以 ``data:`` 开头（大小写敏感）；否则返回 None（空行/注释/其它字段）
    - ``data:`` 后若紧跟一个空格，去掉这一个空格；没有空格也合法
    - 返回剩余字符串（可能是 JSON，也可能是 ``[DONE]``）
    - 注意：``data:`` 本身不够成有效 payload 行约定之外的内容——只要以 data: 开头就返回剩余部分（可为空串）
    """
    # TODO: 实现这里
    raise NotImplementedError


def extract_delta_text(payload: dict[str, Any]) -> str | None:
    """从流式 chunk JSON 中取出增量文本。

    规则：
    - 需要 ``choices`` 为非空 list，且 ``choices[0]`` 为 dict
    - 读取 ``choices[0]["delta"]``；若不是 dict → 返回 None
    - ``delta.get("content")`` 仅当值是 ``str`` 时返回该字符串（允许空串 ``""``）
    - 缺字段 / 类型不对 → 返回 None（调用方应跳过）
    """
    # TODO: 实现这里
    raise NotImplementedError


def print_stream(
    chunks: Iterable[str],
    *,
    file: TextIO | None = None,
) -> str:
    """把增量文本打印到终端（或指定 file），并返回拼接后的完整字符串。

    要求：
    - 每个 chunk 使用 ``print(chunk, end="", flush=True, file=...)``
    - 迭代结束后再 ``print(file=...)`` 输出一个换行
    - 返回 ``"".join(所有 chunk)``
    - ``file`` 默认 ``sys.stdout``
    """
    # TODO: 实现这里
    raise NotImplementedError


class StreamingChatClient:
    """面向 OpenAI 兼容 Chat Completions 的流式薄封装。"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        model: str,
        timeout: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._model = model
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> StreamingChatClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def iter_content(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float | None = None,
    ) -> Iterator[str]:
        """发起流式补全，逐个 yield ``delta.content`` 字符串。

        请求 JSON 必须包含：
        - model: 构造时的模型名
        - messages: [m.to_dict() for m in messages]
        - stream: True   （必须是 JSON boolean true）

        若 temperature 非 None，则写入请求体。

        读取规则：
        - 使用 ``self._client.stream("POST", "/chat/completions", json=payload)``
        - status 不在 200–299 → 先 ``resp.read()`` 再 ``ChatHttpError(status, body_text)``
        - 对 ``resp.iter_lines()`` 的每一行调用 ``parse_sse_data_line``
        - payload 为 ``[DONE]`` → 停止迭代（不要再读后续行）
        - 其它 payload：``json.loads``；失败 → ``ChatResponseError``
        - loads 结果不是 dict → ``ChatResponseError``
        - 用 ``extract_delta_text``；若返回 str（含空串）则 yield；若 None 则跳过
        """
        # TODO: 实现这里
        raise NotImplementedError
        yield  # pragma: no cover  — 让类型检查知道这是 generator


def _as_int(value: Any) -> int | None:
    """预留给后续扩展；今日测试不用。"""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None
