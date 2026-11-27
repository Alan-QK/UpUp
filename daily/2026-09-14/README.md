# Day 38｜拒答与低相关处理

> 日期：2026-09-14（周一）  
> Phase 2 / Week 8 · 学习日序号：**D38 / 120**  
> 建议时长：**75 分钟**（概念 20 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清为什么「有 top-k 命中」≠「可以放心回答」
2. 用 `min_top_score` / `min_margin` 做检索门控，低相关时拒答
3. 保证拒答路径**不调用**生成函数（省钱、防胡扯）
4. 产出前端友好的拒答文案（原因 + 建议）

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 8 · D38）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾：[`../2026-09-11/notes.md`](../2026-09-11/notes.md)

重点抓住三件事：

- **硬门控 vs 软 Prompt**：分数不够直接拒，别只靠「请说不知道」
- **先判分，再生成**：拒答路径零 LLM 调用
- **文案要可产品化**：承认不知道 + 原因 + 下一步

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain / chromadb。

### 任务

1. 完成 `exercise/refusal.py` 中标有 TODO 的函数（`rag_pipeline` / `vector_store` 已给出，勿改）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-09-14/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py
python3 main.py --query "今天天气怎么样"
python3 main.py --query "RAG 为什么能降低幻觉"
python3 main.py --min-score 0.70 --query "前端 SSE"
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] 空命中 / 低分 / 低区分度三种 reason 行为正确
- [ ] 拒答时 **不调用** `generate_fn`
- [ ] `format_refusal` 三行文案与四位小数字符串精确匹配
- [ ] 不引入 LLM SDK / 向量库第三方包

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能解释：向量库几乎总会返回 k 条，为什么还要看分数
- [ ] 我知道门控应放在 Generate **之前**，而不是之后再后悔
- [ ] 我能说出 `low_score` 与 `low_margin` 各自防什么问题
- [ ] 我清楚明天要做什么：用小样例评测检索与拒答（D39）

---

## 通知摘要（便于推送）

**Day 38｜拒答与低相关处理**  
用分数门槛门控检索：不够相关就明确拒答，且不调用生成——质量控制从代码层做起。  
路径：`daily/2026-09-14/`
