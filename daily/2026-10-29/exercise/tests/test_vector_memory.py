"""Day 63 测试：长期向量记忆。"""

from __future__ import annotations

import math

import pytest

from vector_memory import (
    EMBED_DIM,
    KIND_FACT,
    KIND_PREFERENCE,
    MEMORY_MARKER,
    REQUIRED_REPORT_SECTIONS,
    VectorMemoryStore,
    build_demo_preferences,
    cosine_similarity,
    format_memory_block,
    mock_embed,
    render_vector_memory_report,
    seed_demo_store,
)


def test_mock_embed_empty_and_dim() -> None:
    zeros = mock_embed("   ")
    assert zeros == [0.0] * EMBED_DIM
    vec = mock_embed("深色主题")
    assert len(vec) == EMBED_DIM
    assert math.isclose(sum(x * x for x in vec), 1.0, rel_tol=1e-9)


def test_mock_embed_deterministic_and_type() -> None:
    a = mock_embed("TypeScript 优先")
    b = mock_embed("TypeScript 优先")
    assert a == b
    with pytest.raises(TypeError):
        mock_embed(123)  # type: ignore[arg-type]


def test_cosine_similarity_identical_and_orthogonalish() -> None:
    v = mock_embed("中文回答")
    assert math.isclose(cosine_similarity(v, v), 1.0, rel_tol=1e-9)
    assert cosine_similarity([0.0] * EMBED_DIM, v) == 0.0
    with pytest.raises(ValueError):
        cosine_similarity([1.0], [1.0, 2.0])
    with pytest.raises(TypeError):
        cosine_similarity("nope", v)  # type: ignore[arg-type]


def test_upsert_and_user_isolation() -> None:
    store = VectorMemoryStore()
    a = store.remember_preference("u-front", "喜欢深色主题", memory_id="p1")
    store.remember_preference("u-back", "偏好 Go", memory_id="p2")
    assert a.kind == KIND_PREFERENCE
    assert store.size() == 2
    assert store.size("u-front") == 1
    assert store.get("p1") is not None
    assert len(store.list_user("u-front")) == 1
    assert store.list_user("u-front")[0].text == "喜欢深色主题"


def test_upsert_overwrite_same_id() -> None:
    store = VectorMemoryStore()
    store.upsert(user_id="u1", text="旧偏好", kind=KIND_FACT, memory_id="x1")
    store.upsert(user_id="u1", text="新偏好", kind=KIND_PREFERENCE, memory_id="x1")
    assert store.size() == 1
    assert store.get("x1") is not None
    assert store.get("x1").text == "新偏好"
    assert store.get("x1").kind == KIND_PREFERENCE


def test_upsert_rejects_blank_and_bad_kind() -> None:
    store = VectorMemoryStore()
    with pytest.raises(ValueError):
        store.upsert(user_id="  ", text="ok")
    with pytest.raises(ValueError):
        store.upsert(user_id="u1", text="   ")
    with pytest.raises(ValueError):
        store.upsert(user_id="u1", text="ok", kind="mystery")


def test_delete_and_clear() -> None:
    store = seed_demo_store()
    assert store.size("u-front") == 3
    assert store.delete("demo-1") is True
    assert store.delete("missing") is False
    removed = store.clear("u-front")
    assert removed == 2
    assert store.size("u-front") == 0
    assert store.size("u-back") == 2
    assert store.clear() == 2
    assert store.size() == 0


def test_search_prefers_relevant_and_isolates_user() -> None:
    store = seed_demo_store()
    result = store.search("深色模式少动效", user_id="u-front", top_k=2, min_score=0.05)
    assert result.stats.candidate_count == 3
    assert result.stats.returned >= 1
    assert result.hits[0].item.user_id == "u-front"
    joined = " ".join(h.item.text for h in result.hits)
    assert "深色" in joined or "动画" in joined
    # 不应串到 u-back
    assert all(h.item.user_id == "u-front" for h in result.hits)

    back = store.search("Go 语言", user_id="u-back", top_k=1, min_score=0.05)
    assert back.stats.returned == 1
    assert "Go" in back.hits[0].item.text


def test_search_min_score_and_top_k() -> None:
    store = seed_demo_store()
    tight = store.search("深色主题", user_id="u-front", top_k=1, min_score=0.99)
    # 极高阈值时可能 0 命中，也可能因自相似接近 1；至少 returned <= 1
    assert tight.stats.returned <= 1
    assert len(tight.hits) == tight.stats.returned

    wide = store.search("学习 Agent 练习", user_id="u-front", top_k=2, min_score=0.01)
    assert wide.stats.returned <= 2
    assert len(wide.hits) == wide.stats.returned
    if len(wide.hits) >= 2:
        assert wide.hits[0].score >= wide.hits[1].score


def test_search_validation() -> None:
    store = VectorMemoryStore()
    with pytest.raises(ValueError):
        store.search("  ", user_id="u1")
    with pytest.raises(ValueError):
        store.search("q", user_id="  ")
    with pytest.raises(ValueError):
        store.search("q", user_id="u1", top_k=0)


def test_format_memory_block() -> None:
    assert format_memory_block([]) is None
    store = seed_demo_store()
    result = store.search("TypeScript", user_id="u-front", top_k=1, min_score=0.01)
    block = format_memory_block(result.hits)
    assert block is not None
    assert block.startswith(MEMORY_MARKER)
    assert "TypeScript" in block or "中文" in block
    assert result.context_block == block


def test_seed_demo_and_report() -> None:
    prefs = build_demo_preferences()
    assert len(prefs) == 5
    store = seed_demo_store()
    assert store.size() == 5
    result = store.search("中文 TypeScript", user_id="u-front", top_k=2, min_score=0.05)
    report = render_vector_memory_report(result)
    for section in REQUIRED_REPORT_SECTIONS:
        assert f"## {section}" in report
    assert "u-front" in report
