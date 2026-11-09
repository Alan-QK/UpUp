# Day 35｜周挑战：本地笔记检索

> 日期：2026-09-09（周三）  
> Phase 2 / Week 7 · 学习日序号：**D35 / 120**  
> 建议时长：**90 分钟**（概念 20 + Coding 65 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 把 Week 7 的积木（加载 → 切分 → 向量 → Collection）**拼成一条可交付检索闭环**
2. 对本地笔记目录做语义搜索：输入自然语言查询，返回 top-k 片段与来源
3. 说清 CLI 产品形态：索引统计 + 命中列表（score / source / text）
4. 为下周「Retrieve → Augment → Generate」留好接口：今天只检索，不接 LLM 生成

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 7 · D35）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾：[`../2026-09-03/notes.md`](../2026-09-03/notes.md)～[`../2026-09-08/notes.md`](../2026-09-08/notes.md)

重点抓住三件事：

- **周挑战心态**：不引入新框架，把 D31–D34 串起来
- **伪向量够用**：练习用确定性 `fake_embed`，行为可测、零费用
- **检索 ≠ 问答**：今天交付「找片段」；生成答案是 Week 8 的事

---

## Coding 练习（65 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 chromadb / numpy / openai / langchain。

### 任务

1. 完成 `exercise/notes_search.py` 中标有 TODO 的函数（`vector_store` / `fake_embed` / dataclass 已给出，勿改）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-09-09/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py
python3 main.py --k 2 --query "Chroma Collection 怎么 query"
python3 main.py --query "前端 SSE 与工具状态"
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] `discover_notes` 跳过隐藏路径，按相对路径排序
- [ ] `chunk_text` 固定窗口 + overlap；非法参数明确报错
- [ ] `index_notes_dir` 写入 MiniCollection，metadata 含 source/index
- [ ] `search_notes` + `format_hits` 能输出可读 top-k
- [ ] 不引入第三方向量库 / LLM SDK

---

## 参考实现

先自己做。卡住超过 25 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能画出：notes/ → Document → Chunk → Embedding → Collection → top-k hits
- [ ] 我知道为什么 chunk id 要用 `source#index`（稳定、可读、可去重）
- [ ] 我能解释：今天的 score 是相似度，不是「答案正确率」
- [ ] 我清楚下周要接生成：把 hits 塞进 Prompt 才叫 RAG

---

## 本周收口（Week 7）

| Day | 能力 |
|-----|------|
| 31 | 文档加载与清洗 |
| 32 | Chunking（窗口 + overlap） |
| 33 | Embedding API |
| 34 | 向量库 add / query |
| **35** | **本地笔记检索 CLI（周挑战）** |

下一周进入 **RAG 生成与质量**：retrieve + generate、引用、拒答、简易评测。

---

## 通知摘要（便于推送）

**Day 35｜周挑战：本地笔记检索**  
串起加载/切分/伪向量/MiniCollection，做成笔记库语义搜索 CLI（top-k + 来源）。  
路径：`daily/2026-09-09/`
