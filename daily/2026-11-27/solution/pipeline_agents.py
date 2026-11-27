"""Day 72 参考实现：流水线双 Agent（Researcher → Writer）。

全程只用标准库——不调用 LLM。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

# --- 角色 ---

ROLE_RESEARCHER = "researcher"
ROLE_WRITER = "writer"
VALID_ROLES = frozenset({ROLE_RESEARCHER, ROLE_WRITER})

# --- 约束 ---

MIN_TOPIC_LEN = 2
MAX_FINDINGS = 5
MIN_CONFIDENCE = 0.35
DEFAULT_MIN_SCORE = 1

REQUIRED_REPORT_SECTIONS = (
    "何为流水线双 Agent",
    "交接合约",
    "角色边界",
    "今日演示统计",
    "明日预告",
)

_TOKEN_SPLIT = re.compile(r"[^\w\u4e00-\u9fff]+", re.UNICODE)


@dataclass(frozen=True)
class CorpusDoc:
    """语料库中的一篇文档（Researcher 的检索对象）。"""

    doc_id: str
    title: str
    text: str
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.doc_id, str) or not self.doc_id.strip():
            raise ValueError("doc_id must be non-empty str")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be non-empty str")
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("text must be non-empty str")
        if not isinstance(self.tags, tuple):
            raise TypeError("tags must be tuple")


@dataclass(frozen=True)
class Finding:
    """一条调研发现。"""

    source_id: str
    claim: str
    confidence: float

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id must be non-empty str")
        if not isinstance(self.claim, str) or not self.claim.strip():
            raise ValueError("claim must be non-empty str")
        if not isinstance(self.confidence, (int, float)):
            raise TypeError("confidence must be number")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True)
class ResearchBrief:
    """Researcher → Writer 的交接物（合约）。"""

    topic: str
    findings: tuple[Finding, ...]
    researcher_notes: str

    def __post_init__(self) -> None:
        if not isinstance(self.topic, str) or not self.topic.strip():
            raise ValueError("topic must be non-empty str")
        if not isinstance(self.findings, tuple):
            raise TypeError("findings must be tuple")
        if not isinstance(self.researcher_notes, str):
            raise TypeError("researcher_notes must be str")


@dataclass(frozen=True)
class Article:
    """Writer 的成稿。"""

    title: str
    outline: tuple[str, ...]
    body: str
    sources: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be non-empty str")
        if not isinstance(self.outline, tuple) or not self.outline:
            raise ValueError("outline must be non-empty tuple")
        if not isinstance(self.body, str) or not self.body.strip():
            raise ValueError("body must be non-empty str")
        if not isinstance(self.sources, tuple) or not self.sources:
            raise ValueError("sources must be non-empty tuple")


@dataclass(frozen=True)
class TraceEvent:
    """一条可回放的协作事件。"""

    role: str
    action: str
    detail: str

    def __post_init__(self) -> None:
        if self.role not in VALID_ROLES:
            raise ValueError(f"invalid role: {self.role}")
        if not isinstance(self.action, str) or not self.action.strip():
            raise ValueError("action must be non-empty str")
        if not isinstance(self.detail, str):
            raise TypeError("detail must be str")


@dataclass(frozen=True)
class PipelineResult:
    """整条流水线的结果。"""

    brief: ResearchBrief
    article: Article
    trace: tuple[TraceEvent, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.brief, ResearchBrief):
            raise TypeError("brief must be ResearchBrief")
        if not isinstance(self.article, Article):
            raise TypeError("article must be Article")
        if not isinstance(self.trace, tuple) or not self.trace:
            raise ValueError("trace must be non-empty tuple")


@dataclass(frozen=True)
class ScoredDoc:
    """检索命中（带分数）。"""

    doc: CorpusDoc
    score: int


def normalize_topic(text: str) -> str:
    """去掉首尾空白、压缩中间空白。空结果或过短则抛 ValueError。"""
    if not isinstance(text, str):
        raise TypeError("topic must be str")
    topic = " ".join(text.split())
    if len(topic) < MIN_TOPIC_LEN:
        raise ValueError(f"topic too short (min {MIN_TOPIC_LEN})")
    return topic


def tokenize(text: str) -> tuple[str, ...]:
    """简易分词：转小写，按非字母数字/非中文切开。"""
    if not isinstance(text, str):
        raise TypeError("text must be str")
    lowered = text.lower()
    parts = [p for p in _TOKEN_SPLIT.split(lowered) if p]
    # 中文短句可能切不出空格：若整段无分隔且非空，保留整段
    if not parts and lowered.strip():
        parts = [lowered.strip()]
    return tuple(parts)


def build_demo_corpus() -> tuple[CorpusDoc, ...]:
    """固定演示语料。"""
    return (
        CorpusDoc(
            doc_id="vec-chroma",
            title="Chroma 适合本地原型",
            text="Chroma 是嵌入友好的本地向量库，适合快速验证 embedding 检索闭环。",
            tags=("chroma", "embedding", "向量", "本地"),
        ),
        CorpusDoc(
            doc_id="vec-pgvector",
            title="pgvector 适合生产 PostgreSQL",
            text="pgvector 把向量检索放进 PostgreSQL，便于与业务表统一运维。",
            tags=("pgvector", "postgresql", "生产", "向量"),
        ),
        CorpusDoc(
            doc_id="agent-tool",
            title="Tool Calling 与 ReAct",
            text="Agent 通过 tool calling 执行动作；ReAct 用思考-行动-观察循环驱动多步任务。",
            tags=("tool", "react", "agent", "工具"),
        ),
        CorpusDoc(
            doc_id="rag-cite",
            title="RAG 需要引用与拒答",
            text="RAG 回答应附带来源 chunk；低相关时宁可拒答，降低幻觉。",
            tags=("rag", "引用", "幻觉"),
        ),
        CorpusDoc(
            doc_id="frontend-sse",
            title="前端消费 SSE 流式输出",
            text="用 fetch + ReadableStream 消费 SSE，可边到边渲染助手回复。",
            tags=("sse", "流式", "前端"),
        ),
    )


def score_doc(topic_tokens: Sequence[str], doc: CorpusDoc) -> int:
    """给文档打分：正文/tags 正向命中 + tag 作为 topic 子串的反向命中。

    反向命中是为了照顾连续中文主题（如「向量数据库选型」切不出「向量」时，
    仍能靠 doc.tags 里的「向量」命中）。
    """
    if not isinstance(doc, CorpusDoc):
        raise TypeError("doc must be CorpusDoc")
    haystack = f"{doc.title} {doc.text}".lower()
    tag_blob = " ".join(doc.tags).lower()
    topic_joined = "".join(t.lower() for t in topic_tokens)
    score = 0
    for token in topic_tokens:
        t = token.lower()
        if not t:
            continue
        if t in haystack:
            score += 1
        if t in tag_blob:
            score += 1
    for tag in doc.tags:
        tl = tag.lower().strip()
        if tl and tl in topic_joined:
            score += 2
    return score


def search_corpus(
    topic: str,
    corpus: Sequence[CorpusDoc],
    *,
    min_score: int = DEFAULT_MIN_SCORE,
    limit: int = MAX_FINDINGS,
) -> tuple[ScoredDoc, ...]:
    """按分数降序返回命中；同分按 doc_id 升序。"""
    topic_norm = normalize_topic(topic)
    tokens = tokenize(topic_norm)
    if not tokens:
        tokens = (topic_norm.lower(),)

    scored: list[ScoredDoc] = []
    for doc in corpus:
        s = score_doc(tokens, doc)
        if s >= min_score:
            scored.append(ScoredDoc(doc=doc, score=s))

    scored.sort(key=lambda x: (-x.score, x.doc.doc_id))
    if limit < 1:
        raise ValueError("limit must be >= 1")
    return tuple(scored[:limit])


def _first_sentence_or_clip(text: str, max_len: int = 40) -> str:
    clipped = text.strip()
    for sep in ("。", "！", "？", ".", "!", "?"):
        if sep in clipped:
            clipped = clipped.split(sep, 1)[0].strip()
            break
    if len(clipped) > max_len:
        clipped = clipped[:max_len].rstrip() + "…"
    return clipped


def researcher_run(
    topic: str,
    corpus: Sequence[CorpusDoc],
    *,
    trace: list[TraceEvent] | None = None,
) -> ResearchBrief:
    """Researcher：检索语料 → 提炼 findings → 写 notes。"""
    topic_norm = normalize_topic(topic)
    hits = search_corpus(topic_norm, corpus)
    if not hits:
        raise ValueError(f"no corpus hit for topic: {topic_norm}")

    if trace is not None:
        trace.append(
            TraceEvent(
                role=ROLE_RESEARCHER,
                action="search",
                detail=f"命中 {len(hits)} 条",
            )
        )

    findings: list[Finding] = []
    for hit in hits:
        claim = f"{hit.doc.title}：{_first_sentence_or_clip(hit.doc.text)}"
        confidence = min(1.0, 0.4 + 0.1 * hit.score)
        if confidence < MIN_CONFIDENCE:
            confidence = MIN_CONFIDENCE
        findings.append(
            Finding(
                source_id=hit.doc.doc_id,
                claim=claim,
                confidence=float(confidence),
            )
        )

    notes = f"主题「{topic_norm}」已完成检索，供 Writer 成稿；优先引用高置信发现。"
    brief = ResearchBrief(
        topic=topic_norm,
        findings=tuple(findings),
        researcher_notes=notes,
    )

    if trace is not None:
        trace.append(
            TraceEvent(
                role=ROLE_RESEARCHER,
                action="handoff",
                detail=f"findings={len(brief.findings)}",
            )
        )
    return brief


def writer_run(
    brief: ResearchBrief,
    *,
    trace: list[TraceEvent] | None = None,
) -> Article:
    """Writer：只读 Brief，禁止访问语料库。"""
    if not isinstance(brief, ResearchBrief):
        raise TypeError("brief must be ResearchBrief")
    if not brief.findings:
        raise ValueError("empty findings: writer refuses empty handoff")

    title = f"关于{brief.topic}的简报"
    outline_list: list[str] = []
    body_parts: list[str] = [f"# {title}", "", f"> {brief.researcher_notes}", ""]
    sources: list[str] = []

    for finding in brief.findings:
        # 大纲：取 claim 中冒号前标题，否则截断 claim
        if "：" in finding.claim:
            section = finding.claim.split("：", 1)[0].strip()
        elif ":" in finding.claim:
            section = finding.claim.split(":", 1)[0].strip()
        else:
            section = finding.claim[:24].rstrip()
        if not section:
            section = finding.source_id
        outline_list.append(section)
        body_parts.append(f"## {section}")
        body_parts.append(finding.claim)
        body_parts.append(f"（置信度 {finding.confidence:.2f} · 来源 `{finding.source_id}`）")
        body_parts.append("")
        if finding.source_id not in sources:
            sources.append(finding.source_id)

    article = Article(
        title=title,
        outline=tuple(outline_list),
        body="\n".join(body_parts).strip() + "\n",
        sources=tuple(sources),
    )

    if trace is not None:
        trace.append(
            TraceEvent(
                role=ROLE_WRITER,
                action="draft",
                detail=f"sections={len(article.outline)}",
            )
        )
        trace.append(
            TraceEvent(
                role=ROLE_WRITER,
                action="done",
                detail=f"sources={len(article.sources)}",
            )
        )
    return article


def run_pipeline(
    topic: str,
    corpus: Sequence[CorpusDoc] | None = None,
) -> PipelineResult:
    """串起 Researcher → Writer，返回结果与完整 trace。"""
    docs = tuple(corpus) if corpus is not None else build_demo_corpus()
    events: list[TraceEvent] = []
    brief = researcher_run(topic, docs, trace=events)
    article = writer_run(brief, trace=events)
    return PipelineResult(brief=brief, article=article, trace=tuple(events))


def render_trace(trace: Sequence[TraceEvent]) -> str:
    """把 trace 打成多行文本。"""
    lines = [f"[{ev.role}] {ev.action} → {ev.detail}" for ev in trace]
    return "\n".join(lines)


def summarize_pipeline(result: PipelineResult) -> dict[str, object]:
    """结构化摘要。"""
    if not isinstance(result, PipelineResult):
        raise TypeError("result must be PipelineResult")
    return {
        "topic": result.brief.topic,
        "finding_count": len(result.brief.findings),
        "source_ids": list(result.article.sources),
        "title": result.article.title,
        "outline_len": len(result.article.outline),
        "trace_roles": [ev.role for ev in result.trace],
        "trace_actions": [ev.action for ev in result.trace],
    }


def build_demo_topics() -> tuple[str, ...]:
    """三条演示主题。"""
    return (
        "向量数据库选型",
        "Agent 工具调用",
        "前端流式输出",
    )


def render_pipeline_report(results: Sequence[PipelineResult] | None = None) -> str:
    """学习报告（含规定二级标题）。"""
    if results is None:
        items = [run_pipeline(t) for t in build_demo_topics()]
    else:
        items = list(results)
    if not items:
        raise ValueError("results must be non-empty")

    lines: list[str] = [
        "# Day 72 学习报告｜流水线双 Agent",
        "",
        "## 何为流水线双 Agent",
        "流水线 = 专职角色串行交接：Researcher 产出 Brief，Writer 只读 Brief 成稿。",
        "收益来自分工与合约，而不是「多叫一个模型」。",
        "",
        "## 交接合约",
        "交接物是结构化的 `ResearchBrief`（findings + notes），不是一段散文。",
        "空 findings 必须失败；Writer 的 sources 只能来自 Brief。",
        "",
        "## 角色边界",
        "Researcher 可检索语料；Writer **禁止**回头搜库，否则角色重新糊成单 Agent。",
        "用 trace 回放 search → handoff → draft → done。",
        "",
        "## 今日演示统计",
        f"- 主题数：{len(items)}",
        "",
    ]
    for result in items:
        sm = summarize_pipeline(result)
        lines.append(
            f"- {sm['topic']}: findings={sm['finding_count']} "
            f"sources={sm['source_ids']} trace={sm['trace_actions']}"
        )

    lines.extend(
        [
            "",
            "## 明日预告",
            "Day 73 将学习主管-工人模式：Supervisor 按任务类型把活分给不同工人。",
            "",
        ]
    )

    report = "\n".join(lines)
    for section in REQUIRED_REPORT_SECTIONS:
        heading = f"## {section}"
        if heading not in report:
            raise RuntimeError(f"missing report section: {section}")
    return report
