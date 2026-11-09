# Day 68｜Reflection 反思纠错

> 日期：2026-11-06（周五）  
> Phase 4 / Week 14 · 学习日序号：**D68 / 120**  
> 建议时长：**80 分钟**（理论 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清 Reflection / critic 在 Plan-and-Execute 之后补了什么能力
2. 用四态决策（accept / retry / revise / abort）合并多条评审意见
3. 实现带 `max_rounds` 的反思循环：对最差一步做模拟重试
4. 把反思轨迹渲染成可读报告，为明日状态机建模留接口

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-04-memory-multiagent.md`](../../curriculum/phases/phase-04-memory-multiagent.md)（Week 14 · D68）
2. 今日笔记：[`notes.md`](./notes.md)
3. 昨日回顾：[`../2026-11-05/notes.md`](../2026-11-05/notes.md)（执行轨迹长什么样）

重点抓住三件事：

- **critic 产出决策，不直接当执行器**
- **优先级：abort > revise > retry > accept**
- **retry 有上限；skipped 倾向 revise**

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**调用 LLM。

### 任务

1. 完成 `exercise/reflection.py` 中的 TODO  
   （打分 / critique / 合并决策 / 模拟重试 / 反思循环 / 报告）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-11-06/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --case failed
python3 main.py --case weak
python3 main.py --report
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] 优质轨迹首轮即可 `accept`
- [ ] 失败/过短观察能走 `retry` 并在轮次内修复
- [ ] 大面积 `skipped` 倾向 `revise`，不盲重试
- [ ] `max_rounds` 耗尽后给出 `abort`
- [ ] `render_reflection_report` 含规定二级标题
- [ ] 全程标准库

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能解释：Reflection 与「再调一次同一个工具」有何不同
- [ ] 我能写出四态决策的优先级
- [ ] 我知道为何不对 `skipped` 步骤无脑 retry
- [ ] 我已知明日 Day 69：状态机视角看 Agent

---

## 本周预告（Week 14 · 规划与反思）

| Day | 主题 |
|-----|------|
| 66 | 任务分解 Planner |
| 67 | Plan-and-Execute |
| **68** | **Reflection / 自评纠错（今天）** |
| 69 | 状态机视角看 Agent |
| 70 | 周挑战：多步骤研究任务 |

---

## 通知摘要（便于推送）

**Day 68｜Reflection 反思纠错**  
增加 critic 轮：对执行轨迹打分，决定接受、重试、改计划或中止。  
路径：`daily/2026-11-06/`
