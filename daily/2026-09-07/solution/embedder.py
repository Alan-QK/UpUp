"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import httpx


class EmbeddingError(Exception):
    """Embedding 客户端相关错误的基类。"""


class EmbeddingHttpError(EmbeddingError):
    """HTTP 状态码不在 2xx。"""

    def __init__(self, status_code: int, body: str = "") -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {body[:200]}")


class EmbeddingResponseError(EmbeddingError):
    """响应无法按约定协议解析（非法 JSON / 缺字段等）。"""


@dataclass(frozen=True)
class EmbeddingVector:
    index: int
    text: str
    vector: tuple[float, ...]
    dims: int


@dataclass(frozen=True)
class EmbeddingBatchResult:
    model: str
    vectors: tuple[EmbeddingVector, ...]
    prompt_tokens: int | None = None
    total_tokens: int | None = None


def validate_texts(texts: Sequence[str]) -> list[str]:
    if len(texts) == 0:
        raise EmbeddingError("texts must not be empty")
    out: list[str] = []
    for item in texts:
        if not isinstance(item, str):
            raise EmbeddingError("each item must be str")
        if item.strip() == "":
            raise EmbeddingError("text must not be blank")
        out.append(item)
    return out


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) == 0 or len(a) != len(b):
        raise EmbeddingError("vector length mismatch")
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        fx = float(x)
        fy = float(y)
        dot += fx * fy
        norm_a += fx * fx
        norm_b += fy * fy
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


class EmbeddingClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        model: str,
        timeout: float = 30.0,
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

    def __enter__(self) -> EmbeddingClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def embed(self, texts: Sequence[str]) -> EmbeddingBatchResult:
        cleaned = validate_texts(texts)
        payload = {"model": self._model, "input": cleaned}
        resp = self._client.post("/embeddings", json=payload)

        if resp.status_code < 200 or resp.status_code > 299:
            raise EmbeddingHttpError(resp.status_code, resp.text)

        try:
            body = resp.json()
        except Exception as exc:  # noqa: BLE001 - 统一成协议错误
            raise EmbeddingResponseError("response is not valid JSON") from exc

        if not isinstance(body, dict):
            raise EmbeddingResponseError("response JSON must be an object")

        data = body.get("data")
        if not isinstance(data, list):
            raise EmbeddingResponseError("missing data list")

        by_index: dict[int, list[float]] = {}
        for item in data:
            if not isinstance(item, dict):
                raise EmbeddingResponseError("data item must be object")
            idx = item.get("index")
            if not isinstance(idx, int) or isinstance(idx, bool):
                raise EmbeddingResponseError("missing index")
            vec = _as_float_list(item.get("embedding"))
            if vec is None:
                raise EmbeddingResponseError("invalid embedding")
            by_index[idx] = vec

        if set(by_index.keys()) != set(range(len(cleaned))):
            raise EmbeddingResponseError("embedding index mismatch")

        vectors: list[EmbeddingVector] = []
        dims: int | None = None
        for i, text in enumerate(cleaned):
            vec = by_index[i]
            if dims is None:
                dims = len(vec)
            elif len(vec) != dims:
                raise EmbeddingResponseError("inconsistent embedding dims")
            if dims <= 0:
                raise EmbeddingResponseError("embedding dims must be > 0")
            vectors.append(
                EmbeddingVector(
                    index=i,
                    text=text,
                    vector=tuple(vec),
                    dims=dims,
                )
            )

        model = body.get("model")
        if not isinstance(model, str) or not model:
            model = self._model

        usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
        prompt_tokens = _as_int(usage.get("prompt_tokens")) if usage else None
        total_tokens = _as_int(usage.get("total_tokens")) if usage else None

        return EmbeddingBatchResult(
            model=model,
            vectors=tuple(vectors),
            prompt_tokens=prompt_tokens,
            total_tokens=total_tokens,
        )


def batch_embed(
    client: EmbeddingClient,
    texts: Sequence[str],
    *,
    batch_size: int = 64,
) -> EmbeddingBatchResult:
    if batch_size < 1:
        raise EmbeddingError("batch_size must be >= 1")

    cleaned = validate_texts(texts)
    all_vectors: list[EmbeddingVector] = []
    model = client._model  # noqa: SLF001 - 合并结果回退
    prompt_sum = 0
    total_sum = 0
    prompt_ok = True
    total_ok = True

    for start in range(0, len(cleaned), batch_size):
        chunk = cleaned[start : start + batch_size]
        part = client.embed(chunk)
        model = part.model
        for v in part.vectors:
            all_vectors.append(
                EmbeddingVector(
                    index=start + v.index,
                    text=v.text,
                    vector=v.vector,
                    dims=v.dims,
                )
            )
        if part.prompt_tokens is None:
            prompt_ok = False
        else:
            prompt_sum += part.prompt_tokens
        if part.total_tokens is None:
            total_ok = False
        else:
            total_sum += part.total_tokens

    return EmbeddingBatchResult(
        model=model,
        vectors=tuple(all_vectors),
        prompt_tokens=prompt_sum if prompt_ok else None,
        total_tokens=total_sum if total_ok else None,
    )


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def _as_float_list(value: Any) -> list[float] | None:
    if not isinstance(value, list) or not value:
        return None
    out: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            return None
        out.append(float(item))
    return out
