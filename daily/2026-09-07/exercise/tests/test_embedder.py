"""Day 33：EmbeddingClient / batch_embed / cosine_similarity（全部离线 Mock）。"""

from __future__ import annotations

import json

import httpx
import pytest

from embedder import (
    EmbeddingBatchResult,
    EmbeddingClient,
    EmbeddingHttpError,
    EmbeddingResponseError,
    EmbeddingVector,
    batch_embed,
    cosine_similarity,
    validate_texts,
)


def _ok_payload(
    texts: list[str],
    *,
    model: str = "text-embedding-3-small",
    dims: int = 4,
    shuffle: bool = True,
    include_usage: bool = True,
) -> dict:
    data = []
    indices = list(range(len(texts)))
    if shuffle:
        indices = list(reversed(indices))
    for idx in indices:
        # 简单可区分向量：第 idx%dims 维为 1+idx*0.1
        vec = [0.0] * dims
        vec[idx % dims] = 1.0 + idx * 0.1
        data.append(
            {
                "object": "embedding",
                "index": idx,
                "embedding": vec,
            }
        )
    payload: dict = {
        "object": "list",
        "model": model,
        "data": data,
    }
    if include_usage:
        payload["usage"] = {
            "prompt_tokens": 10 * len(texts),
            "total_tokens": 10 * len(texts),
        }
    return payload


def _make_handler(
    *,
    expected_model: str = "text-embedding-3-small",
    expected_key: str = "sk-test",
    response_factory=None,
):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path.endswith("/embeddings")
        auth = request.headers.get("Authorization", "")
        assert auth == f"Bearer {expected_key}"

        body = json.loads(request.content.decode("utf-8") or "{}")
        assert body.get("model") == expected_model
        assert isinstance(body.get("input"), list)

        if response_factory is not None:
            return response_factory(request, body)

        texts = [str(x) for x in body["input"]]
        return httpx.Response(
            200, json=_ok_payload(texts, model=expected_model)
        )

    return handler


def test_validate_texts() -> None:
    assert validate_texts(["a", "b"]) == ["a", "b"]

    with pytest.raises(Exception, match="empty"):
        validate_texts([])

    with pytest.raises(Exception, match="str"):
        validate_texts(["ok", 1])  # type: ignore[list-item]

    with pytest.raises(Exception, match="blank"):
        validate_texts(["ok", "  "])


def test_cosine_similarity_basic() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0

    with pytest.raises(Exception, match="length"):
        cosine_similarity([1.0], [1.0, 2.0])

    with pytest.raises(Exception, match="length"):
        cosine_similarity([], [])


def test_embed_orders_by_index_and_usage() -> None:
    transport = httpx.MockTransport(_make_handler())
    with EmbeddingClient(
        "https://api.test/v1",
        "sk-test",
        model="text-embedding-3-small",
        transport=transport,
    ) as client:
        result = client.embed(["alpha", "beta", "gamma"])

    assert isinstance(result, EmbeddingBatchResult)
    assert result.model == "text-embedding-3-small"
    assert result.prompt_tokens == 30
    assert result.total_tokens == 30
    assert [v.index for v in result.vectors] == [0, 1, 2]
    assert [v.text for v in result.vectors] == ["alpha", "beta", "gamma"]
    assert all(v.dims == 4 for v in result.vectors)
    assert isinstance(result.vectors[0].vector, tuple)
    assert result.vectors[0].vector[0] == pytest.approx(1.0)


def test_embed_sends_input_list() -> None:
    captured: dict = {}

    def factory(request: httpx.Request, body: dict) -> httpx.Response:
        captured["body"] = body
        texts = [str(x) for x in body["input"]]
        return httpx.Response(200, json=_ok_payload(texts, shuffle=False))

    transport = httpx.MockTransport(
        _make_handler(response_factory=factory)
    )
    with EmbeddingClient(
        "https://api.test/v1",
        "sk-test",
        model="text-embedding-3-small",
        transport=transport,
    ) as client:
        client.embed(["一", "二"])

    assert captured["body"]["input"] == ["一", "二"]
    assert captured["body"]["model"] == "text-embedding-3-small"


def test_http_error() -> None:
    def factory(request: httpx.Request, body: dict) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "invalid key"}})

    transport = httpx.MockTransport(_make_handler(response_factory=factory))
    with EmbeddingClient(
        "https://api.test/v1",
        "sk-test",
        model="text-embedding-3-small",
        transport=transport,
    ) as client:
        with pytest.raises(EmbeddingHttpError) as ei:
            client.embed(["hi"])
    assert ei.value.status_code == 401
    assert "invalid key" in ei.value.body


def test_invalid_json_raises() -> None:
    def factory(request: httpx.Request, body: dict) -> httpx.Response:
        return httpx.Response(
            200, text="not-json", headers={"content-type": "text/plain"}
        )

    transport = httpx.MockTransport(_make_handler(response_factory=factory))
    with EmbeddingClient(
        "https://api.test/v1",
        "sk-test",
        model="text-embedding-3-small",
        transport=transport,
    ) as client:
        with pytest.raises(EmbeddingResponseError):
            client.embed(["hi"])


def test_missing_embedding_field_raises() -> None:
    def factory(request: httpx.Request, body: dict) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "model": "text-embedding-3-small",
                "data": [{"index": 0, "embedding": "oops"}],
            },
        )

    transport = httpx.MockTransport(_make_handler(response_factory=factory))
    with EmbeddingClient(
        "https://api.test/v1",
        "sk-test",
        model="text-embedding-3-small",
        transport=transport,
    ) as client:
        with pytest.raises(EmbeddingResponseError):
            client.embed(["hi"])


def test_batch_embed_splits_and_reindexes() -> None:
    calls: list[list[str]] = []

    def factory(request: httpx.Request, body: dict) -> httpx.Response:
        texts = [str(x) for x in body["input"]]
        calls.append(texts)
        return httpx.Response(
            200, json=_ok_payload(texts, model="text-embedding-3-small")
        )

    transport = httpx.MockTransport(
        _make_handler(response_factory=factory)
    )
    texts = ["a", "b", "c", "d", "e"]
    with EmbeddingClient(
        "https://api.test/v1",
        "sk-test",
        model="text-embedding-3-small",
        transport=transport,
    ) as client:
        result = batch_embed(client, texts, batch_size=2)

    assert calls == [["a", "b"], ["c", "d"], ["e"]]
    assert [v.index for v in result.vectors] == [0, 1, 2, 3, 4]
    assert [v.text for v in result.vectors] == texts
    assert result.prompt_tokens == 50  # 10 * 5
    assert result.total_tokens == 50
    assert all(isinstance(v, EmbeddingVector) for v in result.vectors)


def test_batch_embed_rejects_bad_batch_size() -> None:
    transport = httpx.MockTransport(_make_handler())
    with EmbeddingClient(
        "https://api.test/v1",
        "sk-test",
        model="text-embedding-3-small",
        transport=transport,
    ) as client:
        with pytest.raises(Exception, match="batch_size"):
            batch_embed(client, ["a"], batch_size=0)
