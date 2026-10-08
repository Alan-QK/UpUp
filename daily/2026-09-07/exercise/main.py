"""Day 33 手工运行入口：批量 Embedding（支持 --demo 离线）。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys

import httpx

from embedder import EmbeddingClient, batch_embed, cosine_similarity

SAMPLES = [
    "RAG 用检索增强生成，先找相关片段再回答。",
    "检索增强生成会先搜索文档再让模型写答案。",
    "今天天气晴朗，适合出去散步。",
    "向量数据库可以按相似度做 top-k 查询。",
]


def _mask(secret: str) -> str:
    if len(secret) <= 8:
        return "***"
    return f"{secret[:3]}***{secret[-4:]}"


def _demo_vector(text: str, dims: int = 8) -> list[float]:
    """确定性伪向量：相同文本 → 相同向量；相近字面 → 略靠近（仅 demo）。"""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    vals: list[float] = []
    while len(vals) < dims:
        need = dims - len(vals)
        chunk = digest if not vals else hashlib.sha256(digest + bytes(vals)).digest()
        for i in range(0, min(need * 4, len(chunk) - (len(chunk) % 4)), 4):
            raw = struct.unpack_from("!I", chunk, i)[0]
            vals.append((raw / 0xFFFFFFFF) * 2.0 - 1.0)
            if len(vals) >= dims:
                break
        digest = chunk
    # 轻微注入字符 bigram 信号，让近义中文句在 demo 下更像一点
    boost = [0.0] * dims
    for i in range(len(text) - 1):
        h = hash(text[i : i + 2]) % dims
        boost[h] += 0.15
    return [vals[i] + boost[i] for i in range(dims)]


def demo_transport(dims: int = 8) -> httpx.MockTransport:
    """离线 Demo：不访问外网，按文本生成固定维度伪向量。"""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        raw_input = body.get("input")
        if isinstance(raw_input, str):
            inputs = [raw_input]
        else:
            inputs = list(raw_input or [])
        data = []
        # 故意打乱返回顺序，迫使客户端按 index 排序
        order = list(range(len(inputs)))
        order.reverse()
        for idx in order:
            data.append(
                {
                    "object": "embedding",
                    "index": idx,
                    "embedding": _demo_vector(str(inputs[idx]), dims=dims),
                }
            )
        total = sum(max(1, len(str(t)) // 4) for t in inputs) or 1
        return httpx.Response(
            200,
            json={
                "object": "list",
                "model": body.get("model") or "demo-embed",
                "data": data,
                "usage": {"prompt_tokens": total, "total_tokens": total},
            },
        )

    return httpx.MockTransport(handler)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Day 33 · Embedding API Demo")
    p.add_argument(
        "--demo",
        action="store_true",
        help="使用 MockTransport，不访问外网",
    )
    p.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="batch_embed 的批大小",
    )
    p.add_argument(
        "--similar",
        action="store_true",
        help="打印样例两两余弦相似度矩阵（基于本次 embedding）",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.demo:
        base_url = "https://api.test/v1"
        api_key = "sk-demo"
        model = "demo-embed"
        transport = demo_transport()
        print("mode       : demo (MockTransport)")
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        base_url = os.environ.get(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        ).strip()
        model = os.environ.get(
            "OPENAI_EMBED_MODEL", "text-embedding-3-small"
        ).strip()
        if not api_key:
            print(
                "缺少 OPENAI_API_KEY。可先：python3 main.py --demo",
                file=sys.stderr,
            )
            return 2
        transport = None
        print("mode       : live")
        print(f"base_url   : {base_url}")
        print(f"model      : {model}")
        print(f"api_key    : {_mask(api_key)}")

    with EmbeddingClient(
        base_url,
        api_key,
        model=model,
        transport=transport,
    ) as client:
        result = batch_embed(
            client, SAMPLES, batch_size=args.batch_size
        )

    print(f"model      : {result.model}")
    print(f"count      : {len(result.vectors)}")
    print(
        f"tokens     : prompt={result.prompt_tokens} "
        f"total={result.total_tokens}"
    )
    for v in result.vectors:
        head = ", ".join(f"{x:.3f}" for x in v.vector[:4])
        preview = v.text if len(v.text) <= 24 else v.text[:24] + "…"
        print(f"[{v.index}] dims={v.dims} [{head}, …]  {preview}")

    if args.similar:
        print("--- cosine similarity ---")
        n = len(result.vectors)
        for i in range(n):
            row = []
            for j in range(n):
                s = cosine_similarity(
                    result.vectors[i].vector, result.vectors[j].vector
                )
                row.append(f"{s:6.3f}")
            print(f"{i}: " + " ".join(row))

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
