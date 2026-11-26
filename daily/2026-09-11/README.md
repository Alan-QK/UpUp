# Day 37｜引用溯源

> 日期：2026-09-11（周五）  
> Phase 2 / Week 8 · 学习日序号：**D37 / 120**  
> 建议时长：**75 分钟**（概念 20 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清为什么 RAG 产品必须把**答案**和**来源 chunk**绑在一起交付
2. 从答案文本解析 `[1]` / `[2]` 引用标记，并映射回检索命中
3. 产出前端友好的视图模型：`CitedAnswer`（答案 + citations + display）
4. 区分 `mentioned`（只展示文中点到的）与 `all`（展示全部检索命中）

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 8 · D37）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾：[`../2026-09-10/notes.md`](../2026-09-10/notes.md)

重点抓住三件事：

- **可点击的 `[N]`**：标记是答案与资料的桥梁，不是装饰
- **视图模型先行**：先定 `Citation` / `CitedAnswer`，UI 只是渲染
- **两种产品策略**：严格溯源（mentioned）vs 透明检索（all）

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain / chromadb。

### 任务

1. 完成 `exercise/citations.py` 中标有 TODO 的函数（`rag_pipeline` / `vector_store` 已给出，勿改）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-09-11/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py
python3 main.py --k 2 --query "前端 SSE 如何展示引用"
python3 main.py --mode all --query "RAG 为什么能降低幻觉"
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] `parse_cited_ranks` 按首次出现去重，忽略 `[0]`
- [ ] `mode=mentioned` 时空标记 → `(无引用)`；未知 rank 报错
- [ ] `format_sources_block` 格式与四位小数字符串精确匹配
- [ ] 不引入 LLM SDK / 向量库第三方包

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能画出：答案气泡里的 `[1]` → 侧栏 Citation 卡片 的数据流
- [ ] 我知道为什么 `cited_ranks` 要按「首次出现」而不是按分数排序
- [ ] 我能解释 `mentioned` 与 `all` 各自适合什么产品场景
- [ ] 我清楚下周一要做什么：无依据时拒答（D38）

---

## 通知摘要（便于推送）

**Day 37｜引用溯源**  
解析答案中的 `[N]`，把检索命中收成可展示的来源列表，交付带溯源的 CitedAnswer。  
路径：`daily/2026-09-11/`
