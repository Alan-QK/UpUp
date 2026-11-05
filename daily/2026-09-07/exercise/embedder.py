"""Day 33 练习：OpenAI 兼容 Embedding API 客户端 + 批量向量化。

请完成 TODO，使 tests/ 全部通过。
依赖：httpx（可用 MockTransport 离线测试）。
不要引入 openai / langchain SDK。
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import httpx


class EmbeddingError(Exception):
    """Embedding 客户端相关错误的基类。"""


class EmbeddingHttpError(EmbeddingError):
    """HTTP 状态码不在 2xx。

    Attributes:
        status_code: 响应状态码
        body: 响应文本（便于调试；可能为空）
    """

    def __init__(self, status_code: int, body: str = "") -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {body[:200]}")


class EmbeddingResponseError(EmbeddingError):
    """响应无法按约定协议解析（非法 JSON / 缺字段等）。"""


@dataclass(frozen=True)
class EmbeddingVector:
    """单条文本对应的向量。"""

    index: int
    text: str
    vector: tuple[float, ...]
    dims: int


@dataclass(frozen=True)
class EmbeddingBatchResult:
    """一次（或多次切批合并后的）embedding 结果。"""

    model: str
    vectors: tuple[EmbeddingVector, ...]
    prompt_tokens: int | None = None
    total_tokens: int | None = None


def validate_texts(texts: Sequence[str]) -> list[str]:
    """校验并返回 list 副本。

    规则（消息需包含对应关键字，便于测试 match）：
    - texts 为空序列 → EmbeddingError，消息含 \"empty\"
    - 任一元素不是 str → EmbeddingError，消息含 \"str\"
    - 任一字符串 strip 后为空 → EmbeddingError，消息含 \"blank\"
    """
    # TODO
    raise NotImplementedError


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """计算余弦相似度。

    规则：
    - 长度必须相同且 > 0，否则 EmbeddingError，消息含 \"length\"
    - 任一向量 L2 模长为 0 → 返回 0.0（避免除零）
    - 否则返回 dot / (norm_a * norm_b)
    """
    # TODO
    raise NotImplementedError


class EmbeddingClient:
    """面向 OpenAI 兼容 Embeddings 的薄封装。

    约定：
    - base_url 形如 https://api.openai.com/v1
    - 请求 path：/embeddings
    - Header：Authorization: Bearer <api_key>
    - 支持 context manager；transport 可选，供 MockTransport 注入
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        model: str,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        # TODO: 保存 model；创建 httpx.Client
        # 提示：
        #   headers = {
        #       "Authorization": f"Bearer {api_key}",
        #       "Content-Type": "application/json",
        #   }
        #   httpx.Client(base_url=..., timeout=..., headers=..., transport=...)
        raise NotImplementedError

    def close(self) -> None:
        """关闭底层 Client。"""
        # TODO
        raise NotImplementedError

    def __enter__(self) -> EmbeddingClient:
        # TODO: 返回 self
        raise NotImplementedError

    def __exit__(self, *args: object) -> None:
        # TODO: 调用 close()
        raise NotImplementedError

    def embed(self, texts: Sequence[str]) -> EmbeddingBatchResult:
        """对一批文本调用 /embeddings，返回按原文顺序对齐的结果。

        步骤：
        1. cleaned = validate_texts(texts)
        2. POST /embeddings，JSON：
           - model: 构造时的 model
           - input: cleaned（list[str]）
        3. status 不在 200–299 → EmbeddingHttpError(status_code, response.text)
        4. 响应不是 JSON object → EmbeddingResponseError
        5. 解析 data：必须是 list；每项含 index(int) 与 embedding(list of numbers)
        6. 按 index 排序后，与 cleaned 逐一对齐：
           - 若缺某个 index / 多出 index / embedding 非 list → EmbeddingResponseError
           - EmbeddingVector.index 用「在本次 cleaned 中的下标」
           - text 取 cleaned[i]；vector 转为 tuple[float, ...]；dims = len(vector)
           - dims 必须 > 0，且本批所有向量 dims 一致，否则 EmbeddingResponseError
        7. model：优先响应里的 model，缺失则回退构造时的 model
        8. usage.prompt_tokens / usage.total_tokens：有则填入，缺则 None
        """
        # TODO
        raise NotImplementedError


def batch_embed(
    client: EmbeddingClient,
    texts: Sequence[str],
    *,
    batch_size: int = 64,
) -> EmbeddingBatchResult:
    """按 batch_size 切批调用 client.embed，合并为一次逻辑结果。

    规则：
    - batch_size < 1 → EmbeddingError，消息含 \"batch_size\"
    - 先 validate_texts(texts)（与单批相同的空/空白校验）
    - 按顺序切成若干批，每批调用 client.embed
    - 合并后的 EmbeddingVector.index 必须是「全局下标」（0..n-1）
    - model：取最后一批的 model（各批应相同；不做额外校验）
    - prompt_tokens / total_tokens：各批均为 int 则求和；任一为 None → 对应字段为 None
    """
    # TODO
    raise NotImplementedError


def _as_int(value: Any) -> int | None:
    """把 JSON 数字安全转成 int；无法转换则返回 None。"""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def _as_float_list(value: Any) -> list[float] | None:
    """把 JSON 数组安全转成 list[float]；失败返回 None。"""
    if not isinstance(value, list) or not value:
        return None
    out: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            return None
        out.append(float(item))
    return out
