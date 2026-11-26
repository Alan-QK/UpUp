"""Day 32 练习：固定窗口 + overlap 文本切分（RAG Chunking）。

Document / Chunk / 常量约定已给出 —— 请勿修改字段名。
请完成 TODO，使 tests/ 全部通过。
只用标准库。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


class ChunkError(ValueError):
    """切分参数或输入非法。"""


@dataclass(frozen=True)
class Document:
    """待切分文档（可与 Day 31 对齐后的文本对接）。"""

    source: str
    text: str


@dataclass(frozen=True)
class Chunk:
    """切分后的文本块。"""

    source: str
    index: int
    start: int
    end: int
    text: str
    char_count: int


# ---------------------------------------------------------------------------
# 请你实现
# ---------------------------------------------------------------------------


def validate_chunk_params(chunk_size: int, overlap: int) -> None:
    """校验切分参数，非法则抛 ChunkError。

    规则（消息需包含对应关键字，便于测试 match）：
    - chunk_size < 1 → ChunkError，消息含 \"chunk_size\"
    - overlap < 0 → ChunkError，消息含 \"overlap\"
    - overlap >= chunk_size → ChunkError，消息含 \"overlap\" 与 \"chunk_size\"
      （可用一句同时包含两者，例如 \"overlap must be < chunk_size\"）
    """
    # TODO
    raise NotImplementedError


def chunk_text(
    text: str,
    *,
    chunk_size: int = 200,
    overlap: int = 40,
    source: str = "",
) -> list[Chunk]:
    """对单段文本做固定窗口 + overlap 切分。

    算法：
    1. 先 validate_chunk_params(chunk_size, overlap)
    2. 若 text 为空字符串 → 返回 []
    3. step = chunk_size - overlap
    4. start 从 0 开始；反复取 end = min(start + chunk_size, len(text))，
       生成 Chunk：
         - source / index（从 0 递增）
         - start / end（半开区间）
         - text = text[start:end]
         - char_count = end - start（也等于 len(切片)）
    5. 若 end == len(text)：追加该块后停止
       否则：start += step，继续
    """
    # TODO
    raise NotImplementedError


def chunk_document(
    doc: Document,
    *,
    chunk_size: int = 200,
    overlap: int = 40,
) -> list[Chunk]:
    """切分单个 Document，source 取自 doc.source。"""
    # TODO
    raise NotImplementedError


def chunk_corpus(
    docs: Sequence[Document],
    *,
    chunk_size: int = 200,
    overlap: int = 40,
) -> list[Chunk]:
    """按 docs 顺序依次 chunk_document，拼接所有 Chunk。

    注意：每个文档的 index 各自从 0 计（不要做成全局递增）。
    空 docs → []。
    """
    # TODO
    raise NotImplementedError


def chunk_stats(chunks: Sequence[Chunk]) -> dict[str, object]:
    """统计摘要。

    返回：
    {
      \"total_chunks\": int,
      \"total_chars\": int,                 # 各 chunk.char_count 之和
      \"avg_chunk_size\": float,            # total_chars / total_chunks；无 chunk 时为 0.0
      \"by_source\": dict[str, int],        # 各 source 的块数；按 source 名字母序
      \"sources\": list[str],               # 去重后的 source，按首次出现顺序
    }
    """
    # TODO
    raise NotImplementedError
