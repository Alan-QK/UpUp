"""Day 40 tests：MiniRag 里程碑（纯本地，无网络）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from mini_rag import (
    AskResult,
    MiniRag,
    MiniRagError,
    index_documents,
    load_documents,
)
from rag_pipeline import RagMessage
from refusal import RefusalPolicy
from vector_store import MiniChromaClient

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "fixtures" / "kb"
GOLDEN = ROOT / "fixtures" / "golden" / "cases.json"


def test_load_and_index_stats() -> None:
    docs = load_documents(KB)
    assert len(docs) == 4
    sources = {d.source for d in docs}
    assert sources == {
        "frontend.md",
        "prompt_tips.md",
        "python.txt",
        "rag_basics.md",
    }

    client = MiniChromaClient()
    col = client.get_or_create_collection("t-index")
    stats = index_documents(docs, col, chunk_size=400, overlap=40)
    assert stats.documents == 4
    assert stats.chunks == 4  # 短文档 + chunk_size=400 → 每文件一块
    assert set(stats.sources) == sources


def test_from_kb_dir_ask_and_cite() -> None:
    rag = MiniRag.from_kb_dir(KB, collection_name="t-ask")
    assert rag.index_stats is not None
    assert rag.index_stats.chunks >= 4

    result = rag.ask("RAG 为什么能降低幻觉")
    assert isinstance(result, AskResult)
    assert result.refused is False
    assert result.reason == "ok"
    assert result.answer
    assert "来源：" in result.display
    assert any(c.source == "rag_basics.md" for c in result.citations)
    assert result.decision.allow is True
    assert result.decision.top_score is not None
    assert result.decision.top_score >= 0.55


def test_ask_refuses_out_of_domain() -> None:
    rag = MiniRag.from_kb_dir(KB, collection_name="t-refuse")
    result = rag.ask("今天天气怎么样")
    assert result.refused is True
    assert result.reason in {"low_score", "empty"}
    assert result.citations == ()
    assert "无法依据当前资料回答" in result.display
    assert result.decision.allow is False


def test_evaluate_golden_pass_rate() -> None:
    rag = MiniRag.from_kb_dir(KB, collection_name="t-eval")
    report = rag.evaluate(GOLDEN)
    assert report.total == 8
    assert report.pass_rate == 1.0
    assert report.hit_rate == 1.0
    assert report.gate_accuracy == 1.0

    md = rag.evaluate_markdown(GOLDEN)
    assert md.startswith("# RAG Eval Report\n")
    assert "Pass rate: 1.0000" in md


def test_invalid_init_and_empty_question() -> None:
    client = MiniChromaClient()
    col = client.get_or_create_collection("t-bad")
    with pytest.raises(MiniRagError, match="k"):
        MiniRag(col, k=0)
    with pytest.raises(MiniRagError, match="citation_mode"):
        MiniRag(col, citation_mode="maybe")
    with pytest.raises(MiniRagError, match="min_top_score"):
        MiniRag(col, policy=RefusalPolicy(min_top_score=1.5))

    rag = MiniRag(col)
    with pytest.raises(Exception, match="question"):
        rag.ask("   ")


def test_chunk_params_and_custom_generate() -> None:
    docs = load_documents(KB)
    client = MiniChromaClient()
    col = client.get_or_create_collection("t-chunk")
    with pytest.raises(MiniRagError):
        index_documents(docs, col, chunk_size=10, overlap=10)

    calls: list[int] = []

    def gen(messages: list[RagMessage]) -> str:
        calls.append(len(messages))
        return "自定义答案用于测试引用块"

    rag = MiniRag.from_kb_dir(
        KB,
        collection_name="t-gen",
        generate_fn=gen,
        citation_mode="all",
    )
    out = rag.ask("什么是 Retrieve Augment Generate")
    assert out.refused is False
    assert out.answer == "自定义答案用于测试引用块"
    assert "来源：" in out.display
    assert calls == [2]


def test_load_documents_missing_dir() -> None:
    with pytest.raises(MiniRagError, match="not a directory"):
        load_documents(ROOT / "fixtures" / "nope")
