"""Day 72 测试：流水线双 Agent（Researcher → Writer）。"""

from __future__ import annotations

import pytest

from pipeline_agents import (
    MAX_FINDINGS,
    MIN_TOPIC_LEN,
    REQUIRED_REPORT_SECTIONS,
    ROLE_RESEARCHER,
    ROLE_WRITER,
    Article,
    CorpusDoc,
    Finding,
    PipelineResult,
    ResearchBrief,
    TraceEvent,
    build_demo_corpus,
    build_demo_topics,
    normalize_topic,
    render_pipeline_report,
    render_trace,
    researcher_run,
    run_pipeline,
    search_corpus,
    summarize_pipeline,
    tokenize,
    writer_run,
)


def test_normalize_topic() -> None:
    assert normalize_topic("  向量   数据库  ") == "向量 数据库"
    with pytest.raises(TypeError):
        normalize_topic(123)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        normalize_topic(" ")
    with pytest.raises(ValueError):
        normalize_topic("a" * (MIN_TOPIC_LEN - 1))


def test_tokenize_and_search_hits() -> None:
    corpus = build_demo_corpus()
    ids = {d.doc_id for d in corpus}
    assert {"vec-chroma", "vec-pgvector", "agent-tool", "rag-cite", "frontend-sse"} <= ids

    tokens = tokenize("向量数据库选型")
    assert tokens  # 至少有内容

    hits = search_corpus("向量数据库选型", corpus)
    assert hits
    assert hits == tuple(sorted(hits, key=lambda h: (-h.score, h.doc.doc_id)))
    hit_ids = {h.doc.doc_id for h in hits}
    assert "vec-chroma" in hit_ids or "vec-pgvector" in hit_ids
    assert len(hits) <= MAX_FINDINGS


def test_researcher_produces_brief_with_trace() -> None:
    corpus = build_demo_corpus()
    events: list[TraceEvent] = []
    brief = researcher_run("Agent 工具调用", corpus, trace=events)
    assert brief.topic == "Agent 工具调用"
    assert brief.findings
    assert "Writer" in brief.researcher_notes or "成稿" in brief.researcher_notes
    assert all(f.confidence >= 0.35 for f in brief.findings)
    assert [e.action for e in events] == ["search", "handoff"]
    assert all(e.role == ROLE_RESEARCHER for e in events)


def test_researcher_fails_on_no_hit() -> None:
    corpus = (
        CorpusDoc(
            doc_id="only-weather",
            title="今日天气",
            text="晴，气温 20 度。",
            tags=("weather",),
        ),
    )
    with pytest.raises(ValueError, match="no corpus hit"):
        researcher_run("量子引力开题报告XYZ", corpus)


def test_writer_refuses_empty_findings() -> None:
    brief = ResearchBrief(topic="空交接", findings=(), researcher_notes="无")
    with pytest.raises(ValueError, match="empty findings"):
        writer_run(brief)


def test_writer_sources_from_brief_only() -> None:
    brief = ResearchBrief(
        topic="RAG 引用",
        findings=(
            Finding(source_id="rag-cite", claim="RAG 需要引用：低相关时拒答", confidence=0.8),
            Finding(source_id="rag-cite", claim="重复来源应去重", confidence=0.7),
            Finding(source_id="vec-chroma", claim="Chroma：适合原型", confidence=0.6),
        ),
        researcher_notes="供 Writer 成稿",
    )
    events: list[TraceEvent] = []
    article = writer_run(brief, trace=events)
    assert article.title.startswith("关于")
    assert "RAG 引用" in article.title
    assert article.sources == ("rag-cite", "vec-chroma")
    assert len(article.outline) == 3
    assert "rag-cite" in article.body
    assert [e.action for e in events] == ["draft", "done"]
    assert all(e.role == ROLE_WRITER for e in events)


def test_run_pipeline_handoff_and_trace_order() -> None:
    result = run_pipeline("前端流式输出")
    assert isinstance(result, PipelineResult)
    assert result.brief.findings
    assert result.article.sources
    # Writer 的 sources 必须来自 Brief
    brief_sources = {f.source_id for f in result.brief.findings}
    assert set(result.article.sources) <= brief_sources

    roles = [e.role for e in result.trace]
    actions = [e.action for e in result.trace]
    assert roles[:2] == [ROLE_RESEARCHER, ROLE_RESEARCHER]
    assert roles[-2:] == [ROLE_WRITER, ROLE_WRITER]
    assert actions == ["search", "handoff", "draft", "done"]

    text = render_trace(result.trace)
    assert "[researcher] search →" in text
    assert "[writer] done →" in text


def test_summarize_and_demo_topics() -> None:
    topics = build_demo_topics()
    assert topics == ("向量数据库选型", "Agent 工具调用", "前端流式输出")

    result = run_pipeline(topics[0])
    sm = summarize_pipeline(result)
    assert sm["topic"] == "向量数据库选型"
    assert sm["finding_count"] == len(result.brief.findings)
    assert sm["outline_len"] == len(result.article.outline)
    assert sm["trace_actions"] == ["search", "handoff", "draft", "done"]


def test_report_sections() -> None:
    results = [run_pipeline(t) for t in build_demo_topics()]
    report = render_pipeline_report(results)
    for section in REQUIRED_REPORT_SECTIONS:
        assert f"## {section}" in report
    assert "向量数据库选型" in report
    assert "Day 73" in report


def test_article_validation() -> None:
    with pytest.raises(ValueError):
        Article(title="", outline=("a",), body="x", sources=("s",))
    with pytest.raises(ValueError):
        TraceEvent(role="boss", action="x", detail="")
