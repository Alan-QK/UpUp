# Day 33 笔记｜Embedding API

## 1. 今天在 RAG 里的位置

```text
文件目录
  → 加载 & 清洗（D31 Document）
    → Chunking（D32 Chunk）
      → Embedding（今天：文本 → 向量）
        → 向量库写入 / 检索（明天 Chroma）
```

检索要比的不是字符串相等，而是「意思像不像」。Embedding 模型把一段文本压成固定长度的浮点数组；语义接近的文本，向量夹角更小。

## 2. 前端类比

| 前端 | Embedding |
|------|-----------|
| 把商品打成特征向量再做推荐 | 把文本打成向量再做相似检索 |
| `fetch('/api')` + 统一错误处理 | `POST /embeddings` + Http/Parse 分层异常 |
| 列表分页请求，避免一次塞爆 | `batch_size` 切批，避免超时/限流 |
| `id` 回填到原列表项 | 响应用 `index` 对齐回原文顺序 |

你熟悉的「接口契约 + 客户端薄封装」——今天原封不动搬到 Embedding。

## 3. API 长什么样

请求（OpenAI 兼容）：

```http
POST /v1/embeddings
Authorization: Bearer <api_key>
Content-Type: application/json

{
  "model": "text-embedding-3-small",
  "input": ["第一段", "第二段"]
}
```

`input` 可以是单个字符串，也可以是字符串数组（批量）。

响应（示意）：

```json
{
  "object": "list",
  "model": "text-embedding-3-small",
  "data": [
    { "object": "embedding", "index": 1, "embedding": [0.01, -0.02, ...] },
    { "object": "embedding", "index": 0, "embedding": [0.03,  0.01, ...] }
  ],
  "usage": { "prompt_tokens": 12, "total_tokens": 12 }
}
```

注意：

- **`data` 顺序不保证** —— 必须以 `index` 排序后再对齐原文
- `embedding` 是 `number[]`；维度由模型决定（如 1536）
- `usage` 里通常只有 prompt/total（没有 completion）

## 4. 为什么要 batch

把 500 个 chunk 一次塞进 `input` 可能碰到：

- 请求体过大 / 网关超时
- 提供商限流（RPM / TPM）
- 单次失败导致整批重来

做法：按 `batch_size` 切成多批，逐批调用，再按全局顺序拼回去。失败策略今天保持简单：**任一批失败就抛错**（先把契约做对；重试留给工程化阶段）。

## 5. 余弦相似度（为明天检索热身）

对两个向量 \(a, b\)：

\[
\cos(a,b) = \frac{a\cdot b}{\|a\|\,\|b\|}
\]

- 结果大致在 \([-1, 1]\)（很多 embedding 实际落在 \([0,1]\) 附近）
- **越接近 1 越相似**
- 任一向量模长为 0 → 今日约定返回 `0.0`（避免除零）

明天向量库会在内部做类似的距离/相似度计算；今天先手写一遍，建立直觉。

## 6. 和 Chat Completions 的差别（别混）

| | Chat | Embedding |
|--|------|-----------|
| Path | `/chat/completions` | `/embeddings` |
| 输入 | `messages[]` | `input` 文本（或数组） |
| 输出 | 助手文字 | 浮点向量 |
| 计费字段 | prompt + completion | 通常只有 prompt/total |
| 用途 | 生成 / 推理 | 检索 / 聚类 / 去重 |

## 7. 安全提醒（沿用 Day 9）

- API Key 只放环境变量，不写进仓库
- Demo 模式用 `MockTransport`，CI / 无网也能跑
- 日志里不要打印完整向量（太长且无必要）；打印 `dims` 与前几个数即可

## 8. 今日最小对象

```text
EmbeddingVector   # index / text / vector / dims
EmbeddingBatchResult  # model / vectors / prompt_tokens / total_tokens
EmbeddingClient.embed(texts) → EmbeddingBatchResult
batch_embed(client, texts, batch_size) → EmbeddingBatchResult
cosine_similarity(a, b) → float
```

下一步（Day 34）：把 `(chunk 元数据 + vector)` 写入 Chroma，做 top-k 查询。
