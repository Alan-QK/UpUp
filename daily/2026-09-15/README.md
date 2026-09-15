# Day 39｜RAG 简易评测

> 日期：2026-09-15（周二）  
> Phase 2 / Week 8 · 学习日序号：**D39 / 120**  
> 建议时长：**80 分钟**（概念 20 + Coding 55 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清什么是 **golden set**，以及为什么它是 RAG 迭代的「安全带」
2. 区分两类检查：**命中（hit）** 与 **门控（gate / 拒答）**
3. 用 5–10 条样例自动算出 hit rate / gate accuracy / pass rate
4. 输出一份可读的 Markdown 评测表，方便对比阈值改动

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 8 · D39）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾：[`../2026-09-14/notes.md`](../2026-09-14/notes.md)

重点抓住三件事：

- **没有样例集 = 调参靠感觉**：阈值、切分、embedding 一变就瞎
- **答对类看 hit，拒对类看 gate**：两套指标不要混成一个「感觉还行」
- **报告要给人看**：表格 + 比率，方便明日打磨 mini-rag

---

## Coding 练习（55 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain / chromadb。

### 任务

1. 完成 `exercise/rag_eval.py` 中标有 TODO 的函数（`rag_pipeline` / `vector_store` 已给出，勿改）
2. `fixtures/golden/cases.json` 已给 8 条样例，阅读即可；`main.py` 已给齐
3. 跑通测试：

```bash
cd daily/2026-09-15/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py
python3 main.py --min-score 0.70
python3 main.py --k 2 --min-score 0.55
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] 能正确加载 / 校验 golden set（含 duplicate / empty 等错误）
- [ ] hit / refuse 两类样例的 `gate_ok` 与 `hit` 语义正确
- [ ] Markdown 报告表头与四位小数比率格式匹配
- [ ] 默认阈值下自带 golden set 的 `pass_rate == 1.0`
- [ ] 不引入 LLM SDK / 向量库第三方包

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能解释：为什么「答案看起来对」不能替代 golden set
- [ ] 我知道 hit_rate 只统计「应该回答」的样例
- [ ] 我能说出改 `min_top_score` 后，报告里哪一列会先变红
- [ ] 我清楚明天要做什么：打磨并提交 `projects/mini-rag`（D40）

---

## 通知摘要（便于推送）

**Day 39｜RAG 简易评测**  
用 8 条 golden set 自动检查命中与拒答，输出 Markdown 报表——让 RAG 调参可回归。  
路径：`daily/2026-09-15/`
