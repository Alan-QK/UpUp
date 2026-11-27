"""Day 34 手工运行入口：写入伪向量 chunk，做 top-k 查询（无网络）。"""

from __future__ import annotations

import argparse
import hashlib
import math
import struct

from vector_store import MiniChromaClient


CHUNKS = [
    {
        "id": "rag-0",
        "text": "RAG 先检索相关文档片段，再让大模型基于片段生成答案。",
        "metadata": {"source": "rag.md", "index": 0},
    },
    {
        "id": "rag-1",
        "text": "向量数据库按相似度做 top-k 查询，常配合 embedding 使用。",
        "metadata": {"source": "rag.md", "index": 1},
    },
    {
        "id": "weather-0",
        "text": "今天天气晴朗，适合出去散步，记得带水。",
        "metadata": {"source": "life.md", "index": 0},
    },
    {
        "id": "chroma-0",
        "text": "Chroma 的核心是 Collection：add 写入，query 按向量取回最相关结果。",
        "metadata": {"source": "chroma.md", "index": 0},
    },
    {
        "id": "frontend-0",
        "text": "前端可以用 SSE 展示流式回答，并在侧栏列出引用的 chunk 来源。",
        "metadata": {"source": "ui.md", "index": 0},
    },
]


# demo 用的主题锚点：让伪向量在「检索/RAG」查询下更可读（非真实 embedding）
_TOPIC_ANCHORS: list[tuple[str, int]] = [
    ("向量", 0),
    ("检索", 1),
    ("top-k", 1),
    ("topk", 1),
    ("RAG", 2),
    ("rag", 2),
    ("Chroma", 3),
    ("chroma", 3),
    ("Collection", 3),
    ("embedding", 4),
    ("前端", 5),
    ("SSE", 5),
    ("天气", 6),
    ("散步", 6),
]


def fake_embed(text: str, dims: int = 16) -> list[float]:
    """确定性伪向量：相同文本 → 相同向量；共享关键词/bigram 时更靠近（仅 demo）。"""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    vals: list[float] = []
    seed = digest
    while len(vals) < dims:
        for i in range(0, len(seed) - (len(seed) % 4), 4):
            raw = struct.unpack_from("!I", seed, i)[0]
            vals.append((raw / 0xFFFFFFFF) * 2.0 - 1.0)
            if len(vals) >= dims:
                break
        seed = hashlib.sha256(seed).digest()
    boost = [0.0] * dims
    for i in range(len(text) - 1):
        h = hash(text[i : i + 2]) % dims
        boost[h] += 0.08
    lower = text.lower()
    for token, axis in _TOPIC_ANCHORS:
        if token.lower() in lower:
            boost[axis % dims] += 1.6
    vec = [vals[i] * 0.15 + boost[i] for i in range(dims)]
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def build_demo_collection():
    client = MiniChromaClient()
    col = client.get_or_create_collection("notes")
    col.add(
        ids=[c["id"] for c in CHUNKS],
        documents=[c["text"] for c in CHUNKS],
        embeddings=[fake_embed(c["text"]) for c in CHUNKS],
        metadatas=[c["metadata"] for c in CHUNKS],
    )
    return col


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 34 Mini vector store demo")
    parser.add_argument(
        "--query",
        default="如何用向量库做 top-k 检索？",
        help="查询文本（会转成伪向量）",
    )
    parser.add_argument("--k", type=int, default=3, help="top-k")
    args = parser.parse_args()

    col = build_demo_collection()
    q_vec = fake_embed(args.query)
    matches = col.query(query_embeddings=[q_vec], n_results=args.k)[0]

    print(f"collection : {col.name}  count={col.count()}  dims={col.dims}")
    print(f"query      : {args.query}")
    print(f"top-{args.k} hits:")
    for m in matches:
        src = m.metadata.get("source", "?")
        idx = m.metadata.get("index", "?")
        print(
            f"  #{m.rank}  score={m.score:.4f}  id={m.id}  "
            f"source={src}#{idx}"
        )
        print(f"       {m.document}")
    print("ok — 这就是 Chroma add/query 的最小心智模型（内存版）。")


if __name__ == "__main__":
    main()
