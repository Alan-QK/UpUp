# Day 32｜文本切分 Chunking

> 日期：2026-09-04（周五）  
> Phase 2 / Week 7 · 学习日序号：**D32 / 120**  
> 建议时长：**75 分钟**（概念 20 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清为什么 RAG 要把长文切成 **chunk**（检索粒度 vs 上下文完整度）
2. 手写 **固定窗口 + overlap** 切分器，理解 `chunk_size` / `overlap` / `step` 三者关系
3. 为每个 chunk 挂上 `source`、序号与字符偏移，方便后续引用溯源
4. 处理边界：空文本、短文本、非法参数、末尾不足一整窗

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 7 · D32）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾：[`../2026-09-03/notes.md`](../2026-09-03/notes.md)（昨天的干净 Document → 今天切块）

重点抓住三件事：

- **切太大** → 检索噪声高；**切太小** → 语义碎片化
- **overlap** 是为了避免关键句正好落在切缝上丢上下文
- chunk 必须继承昨天的 `source`，否则 Day 37 引用溯源接不上

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

今日只用标准库，无需 pydantic / openai / langchain。

### 任务

1. 完成 `exercise/chunker.py` 中标有 TODO 的函数（`Chunk` / `Document` 已给出，勿改字段名）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-09-04/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py
python3 main.py --size 40 --overlap 10
python3 main.py --stats
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `step = chunk_size - overlap`，按固定步长滑动窗口
- [ ] 每个 `Chunk` 带 `source` / `index` / `start` / `end` / `text`
- [ ] 非法参数（`chunk_size < 1`、`overlap < 0`、`overlap >= chunk_size`）抛 `ChunkError`
- [ ] 空文本 → 空列表；短于 `chunk_size` → 单块
- [ ] 不要引入 langchain text splitter 等库

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能写出：`step = chunk_size - overlap`，并解释 overlap 为何不能 ≥ chunk_size
- [ ] 我知道 chunk 的 `start`/`end` 是相对原文的字符偏移（半开区间）
- [ ] 我能说出过大/过小 chunk 对检索的影响
- [ ] 我清楚明天主题：Embedding API（把 chunk 变成向量）

---

## 通知摘要（便于推送）

**Day 32｜文本切分 Chunking**  
实现固定窗口 + overlap 切分器：校验参数、滑动切片、挂 source/偏移元数据，为向量化铺路。  
路径：`daily/2026-09-04/`
