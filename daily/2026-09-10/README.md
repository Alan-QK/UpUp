# Day 36｜最小 RAG 生成链路

> 日期：2026-09-10（周四）  
> Phase 2 / Week 8 · 学习日序号：**D36 / 120**  
> 建议时长：**75 分钟**（概念 20 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清 RAG 三步：**Retrieve → Augment → Generate**
2. 把检索命中格式化进 Prompt（参考资料区块 + 问题）
3. 用可注入的 `generate_fn` 跑通最小问答（测试零费用）
4. 区分「检索命中」与「生成答案」——后者必须 grounded 在前者

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 8 · D36）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾：[`../2026-09-09/notes.md`](../2026-09-09/notes.md)

重点抓住三件事：

- **Augment 是胶水**：没有规范的上下文拼装，再强的模型也会胡说
- **Generate 可替换**：练习用假函数；以后换成 Chat Completions 客户端即可
- **先闭环再优化**：今天不追求引用 UI / 拒答策略（那是 D37–D38）

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain / chromadb。

### 任务

1. 完成 `exercise/rag_pipeline.py` 中标有 TODO 的函数（`vector_store` / `fake_embed` / `index_kb_dir` / `demo_generate` 已给出，勿改）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-09-10/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py
python3 main.py --k 2 --query "前端 SSE 如何展示引用"
python3 main.py --query "RAG 为什么能降低幻觉"
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] `format_context_block` 空列表返回 `(无相关资料)`；多条格式正确
- [ ] `build_rag_messages` 产出 system + user，且含 SYSTEM_PROMPT
- [ ] `retrieve` + `run_rag` 串起检索与生成；非法 k / 空生成会报错
- [ ] 不引入 LLM SDK / 向量库第三方包

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能默写 RAG 三步，并指出今天代码里对应的三个函数
- [ ] 我知道为什么要用 `GenerateFn` 而不是在练习里写死 OpenAI SDK
- [ ] 我能解释：system 约束「只根据参考资料」如何降低幻觉
- [ ] 我清楚明天要做什么：答案附带来源 chunk（引用溯源）

---

## 通知摘要（便于推送）

**Day 36｜最小 RAG 生成链路**  
实现 retrieve + prompt 拼装 + generate，跑通最小问答（假生成，可测）。  
路径：`daily/2026-09-10/`
