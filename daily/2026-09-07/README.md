# Day 33｜Embedding API

> 日期：2026-09-07（周一）  
> Phase 2 / Week 7 · 学习日序号：**D33 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清 **Embedding** 是什么：把文本变成固定维度的浮点向量，相近语义在空间里更靠近
2. 看懂 OpenAI 兼容的 `/v1/embeddings` 请求/响应，并手写一个薄客户端
3. 实现 **批量向量化**：按 `batch_size` 切批、合并结果、按 `index` 对齐原文
4. 用 **余弦相似度** 做一次离线「谁更像谁」的小演示（为明天向量库打底）

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 7 · D33）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾：[`../2026-09-04/notes.md`](../2026-09-04/notes.md)（昨天的 Chunk → 今天变成向量）
4. 可选回顾：Day 11 ChatClient（同一套 OpenAI 兼容 HTTP 风格）

重点抓住三件事：

- **Chat 输出文字；Embedding 输出向量** —— 接口很像，语义不同
- **一批 input 对应一批 embedding**，响应里用 `index` 对齐，顺序不保证
- 今天先把「文本 → 向量」跑通；**写入向量库**是明天（Day 34）

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest httpx
```

### 任务

1. 完成 `exercise/embedder.py` 中标有 TODO 的部分（dataclass / 异常类已给出，勿改字段名）
2. `main.py` **已给齐**，阅读即可（支持 `--demo` 离线）
3. 跑通测试：

```bash
cd daily/2026-09-07/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --demo --batch-size 2
python3 main.py --demo --similar
```

有真实 Key 时也可：

```bash
export OPENAI_API_KEY=sk-...
# 可选：export OPENAI_BASE_URL=https://api.openai.com/v1
# 可选：export OPENAI_EMBED_MODEL=text-embedding-3-small
python3 main.py
```

### 验收标准

- [ ] `pytest` 全部通过（全部离线 Mock，不访问外网）
- [ ] `POST /embeddings`，Header 带 `Authorization: Bearer ...`
- [ ] 批量：`input` 为字符串列表；结果按 `index` 排回原文顺序
- [ ] HTTP 非 2xx → `EmbeddingHttpError`；坏 JSON / 缺字段 → `EmbeddingResponseError`
- [ ] `batch_embed` 按 `batch_size` 切批并拼接；非法 `batch_size` / 空文本抛错
- [ ] 实现 `cosine_similarity`（含零向量边界）

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 能用一句话向同事解释「向量相近 ≈ 语义相近」
- [ ] 知道响应 `data[i].index` 为什么重要
- [ ] 理解为何要对长列表做 batch（限流 / 超时 / 请求体大小）
- [ ] 余弦相似度公式写得出来，且知道分母为 0 时怎么办
- [ ] 明天要用今天的向量写入 Chroma —— `source` 仍挂在 chunk 侧，今天只管向量本身
