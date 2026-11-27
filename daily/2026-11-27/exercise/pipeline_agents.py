"""Day 72 练习：流水线双 Agent（Researcher → Writer）。

请完成 TODO，使 tests/ 全部通过。
全程只用标准库——不调用 LLM。

提示：
- 数据类与常量已给齐
- 先写 normalize_topic / tokenize / search_corpus
- 再实现 researcher_run / writer_run
- 最后用 run_pipeline 串起来并写报告
"""

from __future__ import annotations

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
    # TODO
    raise NotImplementedError


def tokenize(text: str) -> tuple[str, ...]:
    """简易分词：转小写，按非字母数字/非中文切开，去掉空 token。

    提示：可用正则把分隔符替换成空格再 split；保留中文与 ascii 词。
    至少要让「向量数据库选型」能切出有用片段，或整体作为 token。
    """
    # TODO
    raise NotImplementedError


def build_demo_corpus() -> tuple[CorpusDoc, ...]:
    """固定演示语料（测试会依赖 doc_id / 关键词）。

    必须包含（顺序可自定，但 id 与核心词要在）：
    - vec-chroma：Chroma / 本地原型 / embedding
    - vec-pgvector：pgvector / PostgreSQL / 生产
    - agent-tool：tool calling / ReAct / 工具
    - rag-cite：RAG / 引用 / 幻觉
    - frontend-sse：SSE / 流式 / 前端
    """
    # TODO
    raise NotImplementedError


def score_doc(topic_tokens: Sequence[str], doc: CorpusDoc) -> int:
    """给文档打分。

    规则：
    1. 每个 topic token 若出现在 title/text → +1；若出现在 tags → 再 +1
    2. 额外：若某个 tag 是「拼起来的 topic」的子串 → +2
       （照顾「向量数据库选型」这类连续中文切不出「向量」的情况）
    """
    # TODO
    raise NotImplementedError


def search_corpus(
    topic: str,
    corpus: Sequence[CorpusDoc],
    *,
    min_score: int = DEFAULT_MIN_SCORE,
    limit: int = MAX_FINDINGS,
) -> tuple[ScoredDoc, ...]:
    """按分数降序返回命中；同分按 doc_id 升序。过滤 score < min_score。"""
    # TODO
    raise NotImplementedError


def researcher_run(
    topic: str,
    corpus: Sequence[CorpusDoc],
    *,
    trace: list[TraceEvent] | None = None,
) -> ResearchBrief:
    """Researcher：检索语料 → 提炼 findings → 写 notes。

    规则：
    1. normalize topic
    2. search_corpus；若无命中 → ValueError（不要交空 Brief）
    3. 每条命中变成 Finding：
       - source_id = doc_id
       - claim = 「{title}：{text 首句或前 40 字}」类短陈述
       - confidence = min(1.0, 0.4 + 0.1 * score)，且 ≥ MIN_CONFIDENCE
    4. researcher_notes 需含主题与「供 Writer 成稿」字样
    5. 若传入 trace，追加 search / handoff 两条事件（role=researcher）
    """
    # TODO
    raise NotImplementedError


def writer_run(
    brief: ResearchBrief,
    *,
    trace: list[TraceEvent] | None = None,
) -> Article:
    """Writer：只读 Brief，禁止访问语料库。

    规则：
    1. findings 为空 → ValueError
    2. title = f「关于{topic}的简报」
    3. outline：每条 finding 的 title 部分或 claim 截断成一节；至少 1 节
    4. body：按 outline 生成 Markdown 小节（## + 对应 claim）
    5. sources：findings 的 source_id，去重且保持首次出现顺序
    6. 若传入 trace，追加 draft / done 两条事件（role=writer）
    """
    # TODO
    raise NotImplementedError


def run_pipeline(
    topic: str,
    corpus: Sequence[CorpusDoc] | None = None,
) -> PipelineResult:
    """串起 Researcher → Writer，返回结果与完整 trace。"""
    # TODO
    raise NotImplementedError


def render_trace(trace: Sequence[TraceEvent]) -> str:
    """把 trace 打成多行文本：`[role] action → detail`。"""
    # TODO
    raise NotImplementedError


def summarize_pipeline(result: PipelineResult) -> dict[str, object]:
    """结构化摘要。

    键：topic / finding_count / source_ids / title / outline_len /
        trace_roles / trace_actions
    """
    # TODO
    raise NotImplementedError


def build_demo_topics() -> tuple[str, ...]:
    """三条演示主题（测试按内容断言，不按 index 也可，但建议固定）：

    1. 向量数据库选型
    2. Agent 工具调用
    3. 前端流式输出
    """
    # TODO
    raise NotImplementedError


def render_pipeline_report(results: Sequence[PipelineResult] | None = None) -> str:
    """学习报告（必须包含 REQUIRED_REPORT_SECTIONS 五个二级标题）。"""
    # TODO
    raise NotImplementedError
