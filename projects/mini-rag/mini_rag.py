"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from chunker import Chunk, Document, chunk_document, validate_chunk_params
from citations import Citation, build_cited_answer
from rag_eval import EvalReport, format_report_markdown, load_golden_set, run_eval
from rag_pipeline import (
    EmbedFn,
    GenerateFn,
    RetrievedChunk,
    build_rag_messages,
    demo_generate,
    fake_embed,
    normalize_question,
    retrieve,
)
from refusal import (
    GateDecision,
    RefusalPolicy,
    evaluate_retrieval,
    format_refusal,
    validate_policy,
)
from vector_store import MiniChromaClient, MiniCollection

SUPPORTED_SUFFIXES: tuple[str, ...] = (".txt", ".md", ".markdown")
DEFAULT_CHUNK_SIZE = 400
DEFAULT_OVERLAP = 40
DEFAULT_K = 3


class MiniRagError(ValueError):
    """mini-rag 参数或状态不合法。"""


@dataclass(frozen=True)
class AskResult:
    """一次问答的完整结果（含门控与引用）。"""

    question: str
    refused: bool
    reason: str
    answer: str
    display: str
    contexts: tuple[RetrievedChunk, ...]
    citations: tuple[Citation, ...]
    decision: GateDecision


@dataclass(frozen=True)
class IndexStats:
    """索引统计。"""

    documents: int
    chunks: int
    sources: tuple[str, ...]


def _discover_files(root: Path) -> list[Path]:
    root = root.resolve()
    if not root.is_dir():
        raise MiniRagError("not a directory")
    found: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        found.append(path)
    found.sort(key=lambda p: p.relative_to(root).as_posix())
    return found


def load_documents(root: Path | str) -> list[Document]:
    """加载 kb 目录下的 txt/md 文档。"""
    base = Path(root)
    paths = _discover_files(base)
    if not paths:
        raise MiniRagError("no documents")
    base = base.resolve()
    docs: list[Document] = []
    for path in paths:
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
        text = text.lstrip("\ufeff").strip()
        if not text:
            continue
        source = path.relative_to(base).as_posix()
        docs.append(Document(source=source, text=text))
    if not docs:
        raise MiniRagError("no documents")
    return docs


def index_documents(
    docs: Sequence[Document],
    collection: MiniCollection,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    embed_fn: EmbedFn = fake_embed,
) -> IndexStats:
    """切分并写入向量库。"""
    try:
        validate_chunk_params(chunk_size, overlap)
    except ValueError as exc:
        raise MiniRagError(str(exc)) from exc

    ids: list[str] = []
    documents: list[str] = []
    embeddings: list[list[float]] = []
    metadatas: list[dict[str, object]] = []
    sources: list[str] = []

    for doc in docs:
        chunks: list[Chunk] = chunk_document(
            doc, chunk_size=chunk_size, overlap=overlap
        )
        if not chunks:
            continue
        sources.append(doc.source)
        for ch in chunks:
            chunk_id = f"{ch.source}#{ch.index}"
            ids.append(chunk_id)
            documents.append(ch.text)
            embeddings.append(embed_fn(ch.text))
            metadatas.append(
                {
                    "source": ch.source,
                    "index": ch.index,
                    "start": ch.start,
                    "end": ch.end,
                }
            )

    if not ids:
        raise MiniRagError("no chunks")

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return IndexStats(
        documents=len(sources),
        chunks=len(ids),
        sources=tuple(sources),
    )


class MiniRag:
    """最小 RAG：索引 → 检索 → 门控 → 生成 → 引用。"""

    def __init__(
        self,
        collection: MiniCollection,
        *,
        k: int = DEFAULT_K,
        policy: RefusalPolicy | None = None,
        generate_fn: GenerateFn | None = None,
        citation_mode: str = "all",
        embed_fn: EmbedFn = fake_embed,
        index_stats: IndexStats | None = None,
    ) -> None:
        if isinstance(k, bool) or k < 1:
            raise MiniRagError("k must be >= 1")
        if citation_mode not in ("all", "mentioned"):
            raise MiniRagError("citation_mode must be 'all' or 'mentioned'")
        pol = policy if policy is not None else RefusalPolicy()
        try:
            validate_policy(pol)
        except ValueError as exc:
            raise MiniRagError(str(exc)) from exc

        self._collection = collection
        self._k = k
        self._policy = pol
        self._generate_fn = generate_fn or demo_generate
        self._citation_mode = citation_mode
        self._embed_fn = embed_fn
        self._index_stats = index_stats

    @property
    def k(self) -> int:
        return self._k

    @property
    def policy(self) -> RefusalPolicy:
        return self._policy

    @property
    def citation_mode(self) -> str:
        return self._citation_mode

    @property
    def index_stats(self) -> IndexStats | None:
        return self._index_stats

    @classmethod
    def from_kb_dir(
        cls,
        kb_dir: Path | str,
        *,
        collection_name: str = "mini-rag",
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
        k: int = DEFAULT_K,
        policy: RefusalPolicy | None = None,
        generate_fn: GenerateFn | None = None,
        citation_mode: str = "all",
        embed_fn: EmbedFn = fake_embed,
    ) -> MiniRag:
        """从文档目录构建可问答的 MiniRag。"""
        docs = load_documents(kb_dir)
        client = MiniChromaClient()
        col = client.get_or_create_collection(collection_name)
        stats = index_documents(
            docs,
            col,
            chunk_size=chunk_size,
            overlap=overlap,
            embed_fn=embed_fn,
        )
        return cls(
            col,
            k=k,
            policy=policy,
            generate_fn=generate_fn,
            citation_mode=citation_mode,
            embed_fn=embed_fn,
            index_stats=stats,
        )

    def ask(self, question: str) -> AskResult:
        """单次问答：检索 → 拒答门控 → 生成 → 附加来源。"""
        q = normalize_question(question)
        contexts = retrieve(
            self._collection,
            q,
            k=self._k,
            embed_fn=self._embed_fn,
        )
        decision = evaluate_retrieval(contexts, self._policy)

        if not decision.allow:
            text = format_refusal(
                q,
                decision,
                min_top_score=self._policy.min_top_score,
            )
            return AskResult(
                question=q,
                refused=True,
                reason=decision.reason,
                answer=text,
                display=text,
                contexts=tuple(contexts),
                citations=(),
                decision=decision,
            )

        messages = build_rag_messages(q, contexts)
        raw = self._generate_fn(messages)
        if not isinstance(raw, str):
            raise MiniRagError("generate must return str")
        answer = raw.strip()
        if not answer:
            raise MiniRagError("empty generation")

        # 默认 mode=all：即使答案未写 [n]，也附上全部检索来源
        cited = build_cited_answer(
            q,
            answer,
            contexts,
            mode=self._citation_mode,
        )
        return AskResult(
            question=q,
            refused=False,
            reason="ok",
            answer=cited.answer,
            display=cited.display,
            contexts=tuple(contexts),
            citations=cited.citations,
            decision=decision,
        )

    def evaluate(
        self,
        golden: Path | str,
        *,
        k: int | None = None,
        min_top_score: float | None = None,
    ) -> EvalReport:
        """对 golden set 跑检索命中 + 拒答门控评测。"""
        cases = load_golden_set(golden)
        return run_eval(
            cases,
            self._collection,
            k=self._k if k is None else k,
            min_top_score=(
                self._policy.min_top_score
                if min_top_score is None
                else min_top_score
            ),
        )

    def evaluate_markdown(
        self,
        golden: Path | str,
        *,
        k: int | None = None,
        min_top_score: float | None = None,
    ) -> str:
        """评测并返回 Markdown 报告。"""
        report = self.evaluate(golden, k=k, min_top_score=min_top_score)
        return format_report_markdown(report)
