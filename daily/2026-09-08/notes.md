# Day 34 笔记｜向量库 Chroma 入门

## 1. 今天在 RAG 里的位置

```text
文件目录
  → 加载 & 清洗（D31 Document）
    → Chunking（D32 Chunk）
      → Embedding（D33 文本 → 向量）
        → 向量库写入 / top-k 检索（今天）
          → 下周：Retrieve → Augment → Generate
```

昨天你已经会算「两个向量有多像」。今天把这件事产品化：

1. **写入**：把一批 `(id, 文本, 向量, 元数据)` 存起来  
2. **查询**：给一个查询向量，返回最像的 k 条

这就是向量库的最小闭环。

## 2. 前端类比

| 前端 | 向量库 |
|------|--------|
| 本地搜索索引 / Fuse.js | Collection 里的向量索引 |
| `list.filter + sort + slice(0,k)` | `query(..., n_results=k)` |
| 每条记录带 `id` + payload | `id` + `document` + `metadata` |
| React Query 的 cache key | collection name（不同库隔离） |

你熟悉的「集合 + 查询 + 排序截断」——向量库只是把「相等/包含」换成了「相似度」。

## 3. Chroma 心智模型（真实库长这样）

```python
import chromadb

client = chromadb.Client()                      # 进程内 / 持久化二选一
col = client.create_collection("notes")         # 一个命名集合

col.add(
    ids=["c0", "c1"],
    documents=["第一段文字", "第二段文字"],
    embeddings=[[0.1, 0.2, ...], [0.3, 0.1, ...]],
    metadatas=[{"source": "a.md", "index": 0}, {"source": "a.md", "index": 1}],
)

result = col.query(
    query_embeddings=[[0.11, 0.19, ...]],
    n_results=3,
)
# result["ids"] / ["documents"] / ["metadatas"] / ["distances"]
```

记住四个名词：

| 名词 | 含义 |
|------|------|
| Client | 客户端：管理多个 Collection |
| Collection | 一张「向量表」 |
| add | 写入文档 + 向量 + 元数据 |
| query | 按向量相似度取 top-k |

今天练习**不安装** `chromadb`：你手写一个内存版 `MiniCollection`，API 对齐上述心智，测试与 demo 零依赖。项目里程碑再换真 Chroma / pgvector。

## 4. 为什么元数据不能丢？

检索命中的不只是「一段字」，还要能回答：

- 来自哪个文件？（`source`）
- 是该文件第几块？（`chunk_index`）
- 以后做引用：`答案 ← chunk ← 文件路径`

没有 metadata，RAG 只能说「我在某段文字里看到过」，没法做可点击溯源。

## 5. 相似度 vs 距离

| 指标 | 越大越好？ | 今日约定 |
|------|------------|----------|
| 余弦相似度 cosine similarity | 是（接近 1 更像） | **`score` 用它** |
| 余弦距离 / L2 距离 | 否（越小越像） | 真 Chroma 默认常返回 distance |

前端展示时可以说「相关度 92%」——那更像归一化后的 similarity，而不是裸 distance。

今日 `QueryMatch.score` = 余弦相似度；`rank` 从 1 开始（第 1 名最像）。

## 6. add / query 的边界（练习会考）

**add**

- `ids` / `documents` / `embeddings` / `metadatas` 四条列表长度必须相同
- 同一 Collection 内 **id 不可重复**（重复 → 明确报错；upsert 留给以后）
- 所有 embedding **维度必须一致**（首次 add 定下 dims，后续必须对齐）
- 空列表不允许

**query**

- `n_results < 1` → 报错
- 查询向量维度必须与库内 dims 一致
- 库为空 → 返回 `[]`（不是报错）
- 实际返回条数 = `min(n_results, 库内条数)`
- 同分时：**id 字典序更小的优先**（保证测试稳定）

## 7. 伪代码骨架

```python
def query(self, query_embedding, n_results=3):
    scored = []
    for item in self._items:
        score = cosine_similarity(query_embedding, item.embedding)
        scored.append((score, item.id, item))
    scored.sort(key=lambda t: (-t[0], t[1]))  # 分高优先，同分比 id
    top = scored[:n_results]
    return [
        QueryMatch(id=..., document=..., metadata=..., score=s, rank=i)
        for i, (s, _, item) in enumerate(top, start=1)
    ]
```

## 8. 和真实 Chroma 的差距（心里有数即可）

| 手写 Mini | 真 Chroma |
|-----------|-----------|
| 全量暴力扫 + 排序 | HNSW 等近似近邻索引 |
| 仅内存 | 可持久化到磁盘 |
| 只有 cosine score | 多种 distance 空间 |
| 无过滤 | `where` 元数据过滤 |

原则不变：**先手写最小实现，再引入框架理解其抽象。**

## 9. 今日一句话

> 向量库 = 带相似度排序的 chunk 仓库；先把 add + top-k query 做对，Chroma 只是同款心智的工业实现。

## 10. 明日预告

Day 35（周五周挑战）：本地笔记检索 CLI —— 串起加载 / 切分 /（伪）向量 / 检索，做成可跑的小工具。

---

## 我的记录（请自己填写）

1.  
2.  
3.  
