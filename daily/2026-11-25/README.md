# Day 70｜周挑战：多步研究任务

> 日期：2026-11-25（周三）  
> Phase 4 / Week 14 · 学习日序号：**D70 / 120**  
> 建议时长：**90 分钟**（复盘 20 + Coding 60 + 自检 10）

---

## 今日目标

学完今天，你能够：

1. 把本周四块能力拼成一条**可演示**闭环：Plan → Execute → Reflect →（必要时 Retry）→ Done
2. 用状态机事件串起管线，输出可读的**计划**与**执行轨迹**
3. 对「调研类目标」跑通 happy path，并能注入失败触发一轮 retry
4. 说清：周挑战验收的是「过程可展示」，不是「答案更聪明」

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-04-memory-multiagent.md`](../../curriculum/phases/phase-04-memory-multiagent.md)（Week 14 · D70）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾：Day 66–69 的 `solution/`

重点抓住三件事：

- **先计划后执行**：观众要先看到步骤表，再看逐步观察
- **反思驱动重试**：失败不等于整条管线崩；决策决定下一状态
- **状态路径可回放**：`idle → planning → … → done` 本身就是演示素材

---

## Coding 练习（60 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**调用 LLM。

### 任务

1. 完成 `exercise/research_pipeline.py` 中的 TODO  
   （规划 / 执行 / 评审 / 状态机编排 / 报告）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-11-25/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --goal "调研向量数据库选型"
python3 main.py --retry-demo
python3 main.py --report
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] 调研目标能产出 ≥3 步计划，且依赖串行
- [ ] 执行轨迹含逐步 observation，最终有 deliverable
- [ ] 注入失败时首轮 `retry`，次轮可 `accept`
- [ ] 状态路径含 `planning` / `executing` / `reflecting` / `done`
- [ ] `render_research_report` 含规定二级标题
- [ ] 全程标准库

---

## 参考实现

先自己做。卡住超过 25 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能解释：为什么周挑战强调「计划可展示」而不是「直接给结论」
- [ ] 我能画出：goal → plan → execute → reflect → (retry) → done
- [ ] 我知道 Day 66–69 各自对应管线哪一段
- [ ] 我已知下周 Day 71：何时需要 Multi-Agent

---

## 本周回顾（Week 14 · 规划与反思）

| Day | 主题 |
|-----|------|
| 66 | 任务分解 Planner |
| 67 | Plan-and-Execute |
| 68 | Reflection / 自评纠错 |
| 69 | 状态机视角看 Agent |
| **70** | **周挑战：多步研究任务（今天）** |

---

## 通知摘要（便于推送）

**Day 70｜周挑战：多步研究任务**  
串起计划、执行、反思与状态机，输出可展示的计划与执行结果。  
路径：`daily/2026-11-25/`
