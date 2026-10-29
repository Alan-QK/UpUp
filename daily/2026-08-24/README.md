# Day 23｜CoT 与直接回答对比

> 日期：2026-08-24（周一）  
> Phase 2 / Week 5 · 学习日序号：**D23 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 解释 **直接回答（Direct）** 与 **思维链（Chain-of-Thought, CoT）** 的差别
2. 为同一任务生成两套 Prompt，并约定统一的「最终答案」抽取格式
3. 用纯标准库做一次 **离线对比实验**（mock 输出即可，不必真调 API）
4. 说清：CoT 不是万能；简单题可能更慢更贵，难题才更值得拆步骤

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 5 · D23）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾：Day 21 的「输出格式」约束——今天会用 `最终答案：` 做可解析锚点

重点抓住三件事：

- **Direct**：只吐结论，适合分类、短抽取、明确事实
- **CoT**：先写推理步骤，再给结论，适合多步计算 / 需要核对中间态的任务
- **可比性**：两套策略必须共用同一抽取约定，否则无法公平对比

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 任务

1. 完成 `exercise/cot_lab.py` 中的 TODO
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-08-24/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --demo --case ages
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `normalize_strategy` 只接受 `direct` / `cot`
- [ ] `build_messages` 能按策略生成 `[{role:system},{role:user}]`
- [ ] `extract_final_answer` 能从含 `最终答案：` 的文本中抽出答案
- [ ] `evaluate_run` / `compare_outputs` 能产出可打印的对比报告
- [ ] 全程标准库（不要引入 langchain / openai SDK）

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能用一句话说清 CoT 比 Direct 多了什么、贵在哪里
- [ ] 我知道何时该用 Direct（简单、格式刚、延迟敏感）
- [ ] 我知道对比实验至少要统一：题目、期望答案、答案抽取规则
- [ ] 我已知明天 Day 24：Prompt 注入入门防护
