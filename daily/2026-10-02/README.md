# Day 51｜框架选型原则

> 日期：2026-10-02（周五）  
> Phase 3 / Week 11 · 学习日序号：**D51 / 120**  
> 建议时长：**70 分钟**（概念 25 + Coding 40 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说出 Agent 框架选型的核心原则：**少而精、先手写、再抽象**
2. 用一份固定标准（目标 / 能力 / 成本 / 锁定风险）给项目打分选型
3. 产出一页可读的 **选型笔记 Markdown**（可直接贴进团队文档）
4. 明确：本周先选 **1 个**对照框架，不要同时啃 3 个

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 11 · D51）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾上周手写 Loop：[`../2026-10-01/notes.md`](../2026-10-01/notes.md)

重点抓住三件事：

- **框架解决的是编排与工程便利，不是替代对 Loop 的理解**
- **选型先问目标**：学懂 / 上线 / RAG / 多智能体——目标不同，答案不同
- **限制数量**：本阶段主选 1 个框架深入；第二选择最多作「备胎」

---

## Coding 练习（40 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 langchain / langgraph / openai / llamaindex。

### 任务

1. 完成 `exercise/framework_selection.py` 中的 TODO
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-10-02/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --goal learn_loop
python3 main.py --goal multi_agent --note
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `recommend_framework`：学习 Loop / Python 偏弱时优先 `handwritten`
- [ ] `max_frameworks` 限制主选 + 备胎数量，且备胎 ≠ 主选
- [ ] `render_selection_note` 输出含目标、推荐、理由、弃选、下一步的一页笔记
- [ ] `default_decision_cases` 覆盖至少 4 种目标场景
- [ ] 全程标准库（不要真的装框架）

---

## 参考实现

先自己做。卡住超过 15 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能向同事解释「为什么这周不直接 All-in LangChain」
- [ ] 我知道 handwritten → 框架 的学习顺序，而不是反过来
- [ ] 我能为自己的练习项目写出一页选型笔记
- [ ] 我已知明天 Day 52：用选定思路对照重写手写 Agent（仍可 mock，先理解映射）
