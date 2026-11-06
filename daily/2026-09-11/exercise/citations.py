"""Day 37 练习：引用溯源（答案附带来源 chunk）。

复用 Day 36 的 `rag_pipeline.RetrievedChunk`（已给出，勿改）。
请完成 TODO，使 tests/ 全部通过。
只用标准库 + pytest；不要引入 openai / langchain / chromadb。

前端类比：答案气泡 + 侧栏「引用来源」列表；点击 `[1]` 高亮对应 chunk。
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from rag_pipeline import RetrievedChunk

_CITATION_RE = re.compile(r"\[(\d+)\]")


class CitationError(ValueError):
    """引用参数或状态不合法。"""


@dataclass(frozen=True)
class Citation:
    """一条可展示的引用来源。"""

    rank: int
    source: str
    chunk_id: str
    score: float
    snippet: str


@dataclass(frozen=True)
class CitedAnswer:
    """带引用的完整回答（给 CLI / API / 前端共用的视图模型）。"""

    question: str
    answer: str
    citations: tuple[Citation, ...]
    cited_ranks: tuple[int, ...]
    display: str


def make_snippet(text: str, *, max_chars: int = 72) -> str:
    """把 chunk 正文收成一行短预览。

    规则：
    - max_chars 为 bool 或 <1 → CitationError，消息含 \"max_chars\"
    - 先把 \\r\\n / \\r → \\n，再把换行与连续空白压成单个空格，再 strip
    - 若长度 ≤ max_chars → 原样返回
    - 否则截断到 max_chars 个字符，并追加省略号字符 `…`（注意：总长 = max_chars + 1）
    """
    # TODO
    raise NotImplementedError


def citations_from_chunks(
    chunks: Sequence[RetrievedChunk],
    *,
    max_chars: int = 72,
) -> list[Citation]:
    """把检索命中转为 Citation 列表（保持原顺序）。

    - snippet = make_snippet(chunk.text, max_chars=max_chars)
    - 其余字段从 RetrievedChunk 原样映射（chunk_id ← chunk.chunk_id）
    """
    # TODO
    raise NotImplementedError


def parse_cited_ranks(answer: str) -> list[int]:
    """从答案文本解析引用标记 `[N]`。

    规则：
    - 用正则找所有 `[数字]`（数字为十进制非负整数写法）
    - 只保留 N ≥ 1；`[0]` 忽略
    - 按**首次出现**去重；后续重复的 rank 跳过
    - 无标记 → 空列表
    """
    # TODO
    raise NotImplementedError


def select_citations(
    citations: Sequence[Citation],
    ranks: Sequence[int],
    *,
    mode: str = "mentioned",
) -> list[Citation]:
    """按模式挑出要展示的引用。

    mode：
    - \"all\"：忽略 ranks，返回 citations 的拷贝列表（原顺序）
    - \"mentioned\"：
        - ranks 为空 → 返回 []
        - 按 ranks 的顺序输出对应 Citation
        - 同一 rank 在 ranks 里重复出现时只保留第一次
        - 找不到对应 rank → CitationError，消息含 \"unknown\"
    - 其他 mode → CitationError，消息含 \"mode\"
    """
    # TODO
    raise NotImplementedError


def format_sources_block(citations: Sequence[Citation]) -> str:
    """格式化「来源」区块（给 display / CLI）。

    规则：
    - 空列表 → 精确返回：`(无引用)`
    - 否则：
        来源：
        [1] source=<source> id=<chunk_id> score=<四位小数>
            <snippet>          ← 前面 4 个空格缩进
        （条目之间一个空行；末尾无多余空行）
    """
    # TODO
    raise NotImplementedError


def build_cited_answer(
    question: str,
    answer: str,
    chunks: Sequence[RetrievedChunk],
    *,
    mode: str = "mentioned",
    max_chars: int = 72,
) -> CitedAnswer:
    """把裸答案 + 检索命中组装成带引用的 CitedAnswer。

    流程：
    1. question / answer 先 strip；任一为空 → CitationError，消息分别含 \"question\" / \"empty\"
    2. all_citations = citations_from_chunks(chunks, max_chars=max_chars)
    3. cited_ranks = parse_cited_ranks(answer)   # 始终解析，写入结果
    4. selected = select_citations(all_citations, cited_ranks, mode=mode)
    5. display = answer + \"\\n\\n\" + format_sources_block(selected)
    6. 返回 CitedAnswer(
         question=...,
         answer=strip 后的答案,
         citations=tuple(selected),
         cited_ranks=tuple(cited_ranks),
         display=...,
       )
    """
    # TODO
    raise NotImplementedError
