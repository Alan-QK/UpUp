# Day 66｜任务分解 Planner

> 日期：2026-11-04（周三）  
> Phase 4 / Week 14 · 学习日序号：**D66 / 120**  
> 建议时长：**75 分钟**（理论 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清为什么复杂 Agent 需要先 **Plan** 再 **Execute**
2. 用结构化 `Plan` / `PlanStep` 表示「目标 → 有序步骤」
3. 实现启发式 Planner：按目标类型套模板，并处理过短目标 / 步数上限
4. 把计划渲染成可读 Markdown，为明日执行器留好接口

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-04-memory-multiagent.md`](../../curriculum/phases/phase-04-memory-multiagent.md)（Week 14 · D66）
2. 今日笔记：[`notes.md`](./notes.md)

重点抓住三件事：

- **Planner ≠ 聊天回复**：输出是步骤列表，不是最终答案
- **结构先于智能**：今日用模板；换成 LLM 时只换 `plan_from_goal` 内部
- **依赖要显式**：`S2 depends_on S1`，执行器才知道顺序

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**调用 LLM。

### 任务

1. 完成 `exercise/planner.py` 中的 TODO  
   （normalize / classify / plan_from_goal / render / report）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-11-04/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --goal "调研向量数据库选型"
python3 main.py --report
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] 过短目标（如 `hi`）抛 `ValueError`
- [ ] 分类优先级：coding → writing → ops → research → generic
- [ ] 步骤 id 为 `S1..Sn`，且默认串行依赖
- [ ] 短目标在默认 `max_steps` 下裁成 3 步
- [ ] `render_planner_report` 含规定二级标题
- [ ] 全程标准库

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能解释：为什么「一口气让模型做完」在长任务上容易翻车
- [ ] 我能画出：goal → classify → templates → Plan →（明日）Executor
- [ ] 我知道 `strategy` 字段存在的意义（可观测：用了哪种规划策略）
- [ ] 我已知明日 Day 67：Plan-and-Execute 执行器

---

## 本周预告（Week 14 · 规划与反思）

| Day | 主题 |
|-----|------|
| **66** | **任务分解 Planner（今天）** |
| 67 | Plan-and-Execute |
| 68 | Reflection / 自评纠错 |
| 69 | 状态机视角看 Agent |
| 70 | 周挑战：多步骤研究任务 |

---

## 通知摘要（便于推送）

**Day 66｜任务分解 Planner**  
把模糊目标拆成有序步骤列表（启发式模板，可换成 LLM）。  
路径：`daily/2026-11-04/`
