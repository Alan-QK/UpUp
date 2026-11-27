# Day 35 笔记｜周挑战：本地笔记检索

## 1. 今天在路线图里的位置

```text
Week 7
  D31 加载清洗 ─┐
  D32 Chunking ─┼─→ 今天：拼成「本地笔记语义搜索 CLI」
  D33 Embedding ─┤
  D34 向量库   ─┘
        ↓
Week 8：Retrieve → Augment → Generate（真正的 RAG 问答）
```

周挑战不是学新名词，而是证明：**积木能组装成产品切片**。

## 2. 产品切片长什么样？

用户心智（很像前端的「站内搜索」）：

1. 指定一个笔记目录  
2. 系统建立索引（文件数 / chunk 数）  
3. 输入一句话查询  
4. 得到 top-k 片段：分数、来源文件、原文

今天**到第 4 步为止**。不要急着让 LLM「写答案」——没有可靠检索，生成只会一本正经胡说。

## 3. 前端类比

| 前端 | 今日 CLI |
|------|----------|
| 构建搜索索引（构建期） | `index_notes_dir` |
| 搜索框 onSubmit | `search_notes(query, k)` |
| 结果列表组件 | `format_hits` |
| 每条结果的 permalink | `source#chunk_index` |
| Fuse.js / Algolia | MiniCollection + 伪/真 embedding |

你熟悉「索引构建」和「查询渲染」的分工——RAG 数据层就是这件事。

## 4. 流水线伪代码

```python
paths = discover_notes(root)          # 跳过 .hidden
docs = [load_note(p, root=root) for p in paths]
chunks = flatten(chunk_note(d) for d in docs)
collection.add(
    ids=[f"{c.source}#{c.index}" for c in chunks],
    documents=[c.text for c in chunks],
    embeddings=[embed(c.text) for c in chunks],
    metadatas=[{"source": c.source, "index": c.index, ...}],
)
hits = collection.query(query_embeddings=[embed(q)], n_results=k)
```

今日练习里 `embed` 用 **`fake_embed`**（哈希 + 主题锚点），保证：

- 无网络、无 API Key、可单测  
- 相同文本 → 相同向量  
- 「RAG / 检索」类查询仍能偏向相关笔记（demo 可读）

换成 Day 33 的真 EmbeddingClient，接口不用改——这就是可替换边界。

## 5. 为什么 metadata 仍然关键？

命中的不只是一段字，还要能回答：

- 来自哪个文件？→ `source`  
- 第几块？→ `index`  
- 原文偏移？→ `start` / `end`（可选，利于高亮）

下周做引用时，UI 才能渲染「来自 `rag.md#1`」这种可点击溯源。

## 6. 边界条件（练习会考）

| 场景 | 期望 |
|------|------|
| 隐藏文件 / `.git` 一类路径 | discover 跳过 |
| 空目录 / 无笔记 | 明确报错（`no notes`） |
| 全部切不出 chunk | 报错（`no chunks`） |
| 空查询 / k&lt;1 | 报错 |
| 空库查询 | 返回空命中列表（由 Collection 行为决定） |

## 7. 和「全文关键词搜索」的差别

- 关键词：`query in text` / BM25  
- 语义检索：向量靠近 ≠ 字面包含  

伪 embedding 不是生产方案，但能让你先打通**编排与数据结构**。生产再换真模型与真向量库。

## 8. 今日一句话

> 本地笔记检索 = 目录扫描 + Chunk + Embedding + top-k；先交付「找得到」，再谈「答得好」。

## 9. 明日预告

Day 36：最小 RAG 生成链路 —— 把今天的 hits 塞进 Prompt，让模型基于片段回答。

---

## 我的记录（请自己填写）

1.  
2.  
3.  
