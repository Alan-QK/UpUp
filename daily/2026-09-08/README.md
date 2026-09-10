# Day 34｜向量库 Chroma 入门

> 日期：2026-09-08（周二）  
> Phase 2 / Week 7 · 学习日序号：**D34 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清向量库在 RAG 里干什么：存 `(文档片段 + 向量 + 元数据)`，按相似度做 **top-k** 检索
2. 看懂 Chroma 的核心心智模型：`Client → Collection → add / query`
3. 手写一个 **内存版 Mini Collection**（对齐 Chroma 的 add/query 语义，不装 chromadb）
4. 用昨天的余弦相似度，把 chunk 写入后按查询向量取出最相关的 k 条

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 7 · D34）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾：[`../2026-09-07/notes.md`](../2026-09-07/notes.md)（Embedding → 今天写入库）
4. 可选回顾：[`../2026-09-04/notes.md`](../2026-09-04/notes.md)（Chunk 的 source/index）

重点抓住三件事：

- **向量库 ≠ 关系数据库**：按「像不像」找，不是精确匹配 `WHERE`
- **元数据很重要**：`source` / `chunk_index` 是后面做引用溯源的钥匙
- 今天先打通「写入 + top-k」；真正接 `chromadb` 包是项目阶段的事，概念先对齐

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要** `pip install chromadb`（今天刻意手写最小实现）。

### 任务

1. 完成 `exercise/vector_store.py` 中标有 TODO 的部分（异常类 / dataclass 已给出，勿改字段名）
2. `main.py` **已给齐**，阅读即可（内置伪向量 demo，不访问外网）
3. 跑通测试：

```bash
cd daily/2026-09-08/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py
python3 main.py --k 2
python3 main.py --query "向量检索怎么做 top-k"
```

### 验收标准

- [ ] `pytest` 全部通过（纯内存，无网络）
- [ ] `add`：ids / documents / embeddings / metadatas 长度一致；重复 id 报错；维度不一致报错
- [ ] `query`：按余弦相似度降序取 top-k；空库返回空列表；非法 `n_results` 报错
- [ ] 返回的 `QueryMatch` 含 `id` / `document` / `metadata` / `score` / `rank`（rank 从 1 起）
- [ ] 全程不引入 chromadb / numpy / langchain

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 能画出：Chunk → Embedding → Collection.add → query(top-k)
- [ ] 知道为什么检索结果要带 `source` 元数据（明天/后天做引用要用）
- [ ] 理解「相似度 score」与「距离 distance」是一对镜像概念
- [ ] 知道真实项目用 Chroma/pgvector，但 API 心智模型今天已经对齐
- [ ] 周五周挑战：本地笔记检索 CLI —— 会组合 D31–D34

---

## 通知摘要（便于推送）

**Day 34｜向量库 Chroma 入门**  
手写内存 Collection：写入 chunk 向量与元数据，按余弦相似度做 top-k 查询（对齐 Chroma 心智模型）。  
路径：`daily/2026-09-08/`
