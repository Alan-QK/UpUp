# Day 41｜Chatbot vs Agent

> 日期：2026-09-17（周四）  
> Phase 3 / Week 9 · 学习日序号：**D41 / 120**  
> 建议时长：**70 分钟**（概念 25 + Coding 40 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 用一句话说清：**Chatbot 会聊，Agent 会做事**
2. 从「工具 / 副作用 / 多步行动」三个信号判断场景该归哪一类
3. 产出一份可复用的 **对照表（Markdown）** 与若干带理由的例子
4. 明确：RAG 问答、CoT 长推理本身不等于 Agent——**有行动闭环才算**

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 9 · D41）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾：Phase 2 里程碑 [`../2026-09-16/notes.md`](../2026-09-16/notes.md)——昨天做的是「检索增强生成」，今天起学「工具增强行动」

重点抓住三件事：

- **边界在行动**：能否调用工具、改变外部状态、根据观察继续决策
- **信号法分类**：`needs_tools` / `has_side_effects` → Agent；纯对话/文案 → Chatbot
- **产品选型**：别把所有 LLM 功能都叫 Agent，命名清晰才能选对架构

---

## Coding 练习（40 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain。

### 任务

1. 完成 `exercise/agent_vs_chatbot.py` 中的 TODO
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-09-17/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --classify --tools --side-effects
python3 main.py --table
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `default_comparison_rows` 覆盖至少 5 个维度
- [ ] `render_comparison_markdown` 输出合法 Markdown 表
- [ ] `classify_by_signals`：有工具或副作用 → `agent`，否则 → `chatbot`
- [ ] `ScenarioExample` 的 `expected_kind` 必须与信号分类一致
- [ ] 全程标准库（不要引入 langchain / openai SDK）

---

## 参考实现

先自己做。卡住超过 15 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能向同事讲清 Chatbot 与 Agent 的本质差别（不靠黑话）
- [ ] 我知道「多步推理」≠「多步行动」
- [ ] 我能举出 2 个 Chatbot 例、2 个 Agent 例，并说明判断依据
- [ ] 我已知明天 Day 42：Tool Schema 设计——把「能做事」落成函数契约
