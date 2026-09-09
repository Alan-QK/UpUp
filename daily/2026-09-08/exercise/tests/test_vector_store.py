"""Day 34：MiniCollection / MiniChromaClient（纯内存）。"""

from __future__ import annotations

import pytest

from vector_store import (
    MiniChromaClient,
    MiniCollection,
    QueryMatch,
    VectorStoreError,
    cosine_similarity,
)


def test_cosine_similarity_basic() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0

    with pytest.raises(VectorStoreError, match="length"):
        cosine_similarity([1.0], [1.0, 2.0])

    with pytest.raises(VectorStoreError, match="length"):
        cosine_similarity([], [])


def test_add_and_count_and_query_topk() -> None:
    col = MiniCollection("notes")
    col.add(
        ids=["a", "b", "c"],
        documents=["alpha rag", "beta weather", "gamma vector"],
        embeddings=[
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        metadatas=[
            {"source": "a.md", "index": 0},
            {"source": "b.md", "index": 0},
            {"source": "c.md", "index": 0},
        ],
    )
    assert col.count() == 3
    assert col.dims == 3

    hits = col.query(query_embeddings=[[0.9, 0.1, 0.0]], n_results=2)
    assert len(hits) == 1
    assert [m.id for m in hits[0]] == ["a", "b"]
    assert hits[0][0].rank == 1
    assert hits[0][1].rank == 2
    assert hits[0][0].metadata["source"] == "a.md"
    assert isinstance(hits[0][0], QueryMatch)
    assert hits[0][0].score > hits[0][1].score


def test_add_validations() -> None:
    col = MiniCollection("x")

    with pytest.raises(VectorStoreError, match="empty"):
        col.add(ids=[], documents=[], embeddings=[])

    with pytest.raises(VectorStoreError, match="length"):
        col.add(
            ids=["a"],
            documents=["ok", "nope"],
            embeddings=[[1.0, 0.0]],
        )

    with pytest.raises(VectorStoreError, match="metadata"):
        col.add(
            ids=["a"],
            documents=["ok"],
            embeddings=[[1.0]],
            metadatas=[{}, {}],
        )

    with pytest.raises(VectorStoreError, match="id"):
        col.add(
            ids=["  "],
            documents=["ok"],
            embeddings=[[1.0]],
        )

    with pytest.raises(VectorStoreError, match="document"):
        col.add(
            ids=["a"],
            documents=["  "],
            embeddings=[[1.0]],
        )

    col.add(
        ids=["a"],
        documents=["first"],
        embeddings=[[1.0, 0.0]],
    )
    with pytest.raises(VectorStoreError, match="duplicate"):
        col.add(
            ids=["a"],
            documents=["again"],
            embeddings=[[0.0, 1.0]],
        )

    with pytest.raises(VectorStoreError, match="dims"):
        col.add(
            ids=["b"],
            documents=["second"],
            embeddings=[[1.0, 0.0, 0.0]],
        )

    with pytest.raises(VectorStoreError, match="embedding"):
        col.add(
            ids=["c"],
            documents=["third"],
            embeddings=[[1.0, True]],  # type: ignore[list-item]
        )


def test_query_empty_collection_and_n_results() -> None:
    col = MiniCollection("empty")
    assert col.query(query_embeddings=[[1.0, 0.0]], n_results=3) == [[]]

    col.add(
        ids=["a", "b"],
        documents=["one", "two"],
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
    )

    with pytest.raises(VectorStoreError, match="n_results"):
        col.query(query_embeddings=[[1.0, 0.0]], n_results=0)

    with pytest.raises(VectorStoreError, match="n_results"):
        col.query(query_embeddings=[[1.0, 0.0]], n_results=True)  # type: ignore[arg-type]

    with pytest.raises(VectorStoreError, match="empty"):
        col.query(query_embeddings=[], n_results=1)

    with pytest.raises(VectorStoreError, match="dims"):
        col.query(query_embeddings=[[1.0, 0.0, 0.0]], n_results=1)

    # n_results 大于库大小时截断
    hits = col.query(query_embeddings=[[1.0, 0.0]], n_results=10)
    assert len(hits[0]) == 2


def test_tie_break_by_id() -> None:
    col = MiniCollection("tie")
    col.add(
        ids=["b", "a"],
        documents=["same-b", "same-a"],
        embeddings=[[1.0, 0.0], [1.0, 0.0]],
    )
    hits = col.query(query_embeddings=[[1.0, 0.0]], n_results=2)[0]
    assert [m.id for m in hits] == ["a", "b"]
    assert hits[0].score == pytest.approx(hits[1].score)


def test_metadata_default_and_isolation() -> None:
    col = MiniCollection("meta")
    external = {"source": "x.md", "index": 1}
    col.add(
        ids=["a"],
        documents=["hello"],
        embeddings=[[1.0, 0.0]],
        metadatas=[external],
    )
    external["source"] = "mutated.md"
    hits = col.query(query_embeddings=[[1.0, 0.0]], n_results=1)[0]
    assert hits[0].metadata["source"] == "x.md"

    col2 = MiniCollection("meta2")
    col2.add(
        ids=["z"],
        documents=["no-meta"],
        embeddings=[[0.0, 1.0]],
    )
    assert col2.query(query_embeddings=[[0.0, 1.0]], n_results=1)[0][0].metadata == {}


def test_client_create_and_list() -> None:
    client = MiniChromaClient()
    a = client.create_collection("notes")
    assert a.name == "notes"

    with pytest.raises(VectorStoreError, match="exists"):
        client.create_collection("notes")

    same = client.get_or_create_collection("notes")
    assert same is a

    b = client.get_or_create_collection("docs")
    assert b is not a
    assert client.list_collections() == ["docs", "notes"]

    with pytest.raises(VectorStoreError, match="name"):
        MiniCollection("  ")


def test_multi_query() -> None:
    col = MiniCollection("multi")
    col.add(
        ids=["x", "y"],
        documents=["east", "north"],
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
        metadatas=[{"i": 0}, {"i": 1}],
    )
    out = col.query(
        query_embeddings=[[1.0, 0.0], [0.0, 1.0]],
        n_results=1,
    )
    assert [m.id for m in out[0]] == ["x"]
    assert [m.id for m in out[1]] == ["y"]
