# Day 67｜Plan-and-Execute

> 日期：2026-11-05（周四）  
> Phase 4 / Week 14 · 学习日序号：**D67 / 120**  
> 建议时长：**80 分钟**（理论 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清 Plan-and-Execute 与「一口气边想边做」的差别
2. 按 `depends_on` 逐步调用工具，并维护 `ExecutionState` 黑板
3. 正确处理 DONE / FAILED / SKIPPED 与 `stop_on_failure` / `max_steps`
4. 把执行轨迹渲染成可读 Markdown，为明日 Reflection 留接口

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-04-memory-multiagent.md`](../../curriculum/phases/phase-04-memory-multiagent.md)（Week 14 · D67）
2. 今日笔记：[`notes.md`](./notes.md)
3. 昨日回顾：[`../2026-11-04/notes.md`](../2026-11-04/notes.md)（Planner 输出什么）

重点抓住三件事：

- **执行器吃 Plan，不重新发明步骤**
- **依赖只认 DONE**：失败的上游会卡住下游
- **context 是黑板**：工具之间靠共享状态传材料

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**调用 LLM。

### 任务

1. 完成 `exercise/executor.py` 中的 TODO  
   （registry / deps / invoke / execute_plan / render / report）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-11-05/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --goal "调研向量数据库选型"
python3 main.py --max-steps 2 --goal "实现带重试的客户端"
python3 main.py --report
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] 串行计划能跑到 `stop_reason=completed` 且写出 `deliverable`
- [ ] 工具失败时后续步骤为 `skipped`，`stop_reason=failed`
- [ ] `max_steps` 只限制实际工具调用次数
- [ ] `render_executor_report` 含规定二级标题
- [ ] 全程标准库

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能解释：为什么要把 Plan 与 Execute 拆开
- [ ] 我能画出：Plan → deps 检查 → tool → results/context → 下一 step
- [ ] 我知道 `FAILED` 的步骤不能当作下游依赖已满足
- [ ] 我已知明日 Day 68：Reflection 反思纠错

---

## 本周预告（Week 14 · 规划与反思）

| Day | 主题 |
|-----|------|
| 66 | 任务分解 Planner |
| **67** | **Plan-and-Execute（今天）** |
| 68 | Reflection / 自评纠错 |
| 69 | 状态机视角看 Agent |
| 70 | 周挑战：多步骤研究任务 |

---

## 通知摘要（便于推送）

**Day 67｜Plan-and-Execute**  
按计划逐步调用工具，维护执行轨迹与共享黑板。  
路径：`daily/2026-11-05/`
