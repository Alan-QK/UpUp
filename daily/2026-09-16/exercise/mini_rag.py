"""Day 40 练习：MiniRag 编排层（Phase 2 里程碑核心）。

把 D31–D39 的积木收成一条可演示链路：
文档加载 → 切分 → 向量索引 → 检索 → 拒答门控 → 生成 → 引用。

请完成 TODO，使 tests/ 全部通过。
只用标准库 + pytest；不要引入 openai / langchain / chromadb。

已给出、今日勿改：
  chunker.py / vector_store.py / rag_pipeline.py /
  citations.py / refusal.py / rag_eval.py
"""

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
    """发现 kb 下的 txt/md 文件（跳过隐藏路径分量，按相对 posix 排序）。"""
    # TODO: 实现发现逻辑（可参考 rag_pipeline._discover_files）
    raise NotImplementedError


def load_documents(root: Path | str) -> list[Document]:
    """加载 kb 目录下的文档为 Document(source, text)。

    规则：
    - 目录不存在 / 非目录 → MiniRagError("not a directory")
    - 无匹配文件或全部空白 → MiniRagError("no documents")
    - 清洗：统一换行、去 BOM、strip；空白文件跳过
    - source = 相对 root 的 posix 路径
    """
    # TODO
    raise NotImplementedError


def index_documents(
    docs: Sequence[Document],
    collection: MiniCollection,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    embed_fn: EmbedFn = fake_embed,
) -> IndexStats:
    """切分文档并写入向量库。

    规则：
    - 先 validate_chunk_params；失败包装为 MiniRagError
    - 对每个 Document 调 chunk_document
    - id = f"{source}#{index}"
    - metadata 含 source / index / start / end
    - 无任何 chunk → MiniRagError("no chunks")
    - 返回 IndexStats(documents=有切出块的文档数, chunks=总块数, sources=有序)
    """
    # TODO
    raise NotImplementedError


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
        """初始化。

        规则：
        - k < 1 或 bool → MiniRagError("k must be >= 1")
        - citation_mode 仅允许 'all' | 'mentioned'
        - policy 默认 RefusalPolicy()；validate_policy 失败 → MiniRagError
        - generate_fn 默认 demo_generate
        """
        # TODO
        raise NotImplementedError

    @property
    def k(self) -> int:
        # TODO
        raise NotImplementedError

    @property
    def policy(self) -> RefusalPolicy:
        # TODO
        raise NotImplementedError

    @property
    def citation_mode(self) -> str:
        # TODO
        raise NotImplementedError

    @property
    def index_stats(self) -> IndexStats | None:
        # TODO
        raise NotImplementedError

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
        """从文档目录构建 MiniRag：load → index → 返回实例。"""
        # TODO
        raise NotImplementedError

    def ask(self, question: str) -> AskResult:
        """单次问答。

        流程：
        1. normalize_question
        2. retrieve(..., k=self.k, embed_fn=...)
        3. evaluate_retrieval(contexts, policy)
        4. 若不允许：format_refusal → AskResult(refused=True, citations=())
        5. 若允许：build_rag_messages → generate_fn → strip
           - 非 str → MiniRagError("generate must return str")
           - 空 → MiniRagError("empty generation")
           - build_cited_answer(..., mode=citation_mode)
           - 返回 AskResult(refused=False, display=cited.display, ...)
        """
        # TODO
        raise NotImplementedError

    def evaluate(
        self,
        golden: Path | str,
        *,
        k: int | None = None,
        min_top_score: float | None = None,
    ) -> EvalReport:
        """对 golden set 跑 run_eval（默认用实例的 k / policy.min_top_score）。"""
        # TODO
        raise NotImplementedError

    def evaluate_markdown(
        self,
        golden: Path | str,
        *,
        k: int | None = None,
        min_top_score: float | None = None,
    ) -> str:
        """评测并返回 Markdown 报告字符串。"""
        # TODO
        raise NotImplementedError
