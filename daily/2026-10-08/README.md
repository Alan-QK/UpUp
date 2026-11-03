# Day 55｜周挑战：手写 vs 框架对比

> 日期：2026-10-08（周四）  
> Phase 3 / Week 11 · 学习日序号：**D55 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 用固定维度对比 **手写 Agent** 与 **框架层 Agent**（可控性、速度、清晰度、扩展、排错、锁定风险）
2. 结合 Week 11（选型 → 迷你框架 → 业务工具 → 流式事件）写出一份可读的 **对比报告**
3. 按目标（学懂 Loop / 上线 / 面试讲解 / 带新人）给出明确主选，而不是「都挺好」
4. 沉淀可复用的决策口径，方便下周进入安全与里程碑阶段

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 11 · D55）
2. 今日笔记：[`notes.md`](./notes.md)
3. 本周回顾：[`../2026-10-02/notes.md`](../2026-10-02/notes.md) · [`../2026-10-05/notes.md`](../2026-10-05/notes.md) · [`../2026-10-06/notes.md`](../2026-10-06/notes.md) · [`../2026-10-07/notes.md`](../2026-10-07/notes.md)

重点抓住三件事：

- **对比要有尺子**：没有维度的「手写更好 / 框架更快」都是口号
- **同能力对照**：比的是同一套 Loop / 工具 / 事件能力，不是比文档星标数
- **目标决定赢家**：学懂与面试偏手写；赶交付与团队协作偏框架——先说场景再下结论

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 langchain / langgraph / openai / llamaindex。

### 任务

1. 完成 `exercise/comparison_report.py` 中的 TODO  
   （维度常量、默认评分、胜负统计、按目标推荐、Markdown 报告渲染）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-10-08/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --goal learn_loop
python3 main.py --goal ship_product --report
python3 main.py --goal interview --report
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] `week11_default_scores` 覆盖全部 6 个维度，分数在 1–5
- [ ] `recommend_for_goal`：学懂/面试 → handwritten；上线/带新人 → framework
- [ ] `render_comparison_report` 含本周回顾、对照维度、两侧优势、决策建议、下周预告
- [ ] 报告里能看出「谁赢哪一维」，而不是空话对比
- [ ] 全程标准库

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能用 6 个维度向同事讲清手写与框架各自强在哪
- [ ] 我能为「学习转型」与「两周上线」分别给出不同主选
- [ ] 我知道迷你框架的价值：对照理解，而不是替代真框架选型
- [ ] 我已知下周 Day 56：Prompt Injection 案例集

---

## 本周回顾（Week 11）

| Day | 主题 |
|-----|------|
| 51 | 框架选型原则（少而精） |
| 52 | 框架重写手写 Agent |
| 53 | 自定义工具接入框架 |
| 54 | 流式事件与工具状态 |
| **55** | **周挑战：手写 vs 框架对比（今天）** |

---

## 通知摘要（便于推送）

**Day 55｜周挑战：手写 vs 框架对比**  
用固定维度给 Week 11 做认知沉淀，生成一份可决策的对比报告（学懂偏手写，上线偏框架）。  
路径：`daily/2026-10-08/`
