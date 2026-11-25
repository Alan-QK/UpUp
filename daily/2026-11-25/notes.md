# Day 70 笔记｜周挑战：多步研究任务

## 1. 一句话定位

**多步研究任务**：把「模糊调研目标」拆成可见计划，逐步执行 mock 工具，经反思后交付摘要——全程状态可回放。

## 2. 本周能力拼装图

```text
goal
  │
  ├─① Planner（Day66）──► Plan / PlanStep（可打印）
  │
  ├─② Executor（Day67）─► StepResult[] + deliverable + context 黑板
  │
  ├─③ Reflection（Day68）► accept / retry / abort
  │         │
  │         └─ retry ──► 再执行薄弱步骤
  │
  └─④ FSM（Day69）──────► idle→planning→executing→reflecting→done
```

| Day | 积木 | 今天怎么用 |
|-----|------|-----------|
| 66 | Planner | `build_research_plan`：调研模板 4–5 步 |
| 67 | Executor | mock 工具写 observation / deliverable |
| 68 | Reflection | 失败 / 空观察 → retry；否则 accept |
| 69 | 状态机 | 用事件串起管线并记录 `state_path` |
| **70** | **研究闭环** | `run_research_task` 一键演示 |

## 3. 前端迁移直觉

| 你熟悉的前端 | 今日对应 |
|--------------|----------|
| 多步向导 / Stepper | Plan 步骤列表 |
| Loading + 步骤进度条 | 执行中逐步 `running → done` |
| 错误边界 + Retry 按钮 | Reflection 的 `retry` |
| Redux / XState 状态图 | `state_path` 回放 |
| 成功页展示「做了什么」 | 报告里的计划 + 轨迹表 |

结论：Agent 演示页 ≈ **Stepper + 日志面板 + 终态徽章**，不是一个巨大的「思考中…」。

## 4. 为什么「计划必须可见」

只展示最终答案时，观众无法判断 Agent 是否：

- 漏做了检索
- 跳过了对比
- 用幻觉补全了材料

可见计划解决三个产品问题：

1. **信任**：我知道它打算干什么
2. **干预**：HITL 可在某步前叫停（本周已建模，今日演示主路径）
3. **调试**：失败时指到具体 step_id

## 5. 今日简化约定（教学用）

- 只覆盖 **research** 类目标；coding/ops 模板留给里程碑项目
- 工具全部 mock，确定性输出，方便 pytest
- Reflection 用启发式：有 `failed` / 空观察 → `retry`；否则 `accept`
- 注入失败仅第一轮：`inject_fail_step` 模拟工具炸一次，第二轮自动修好

生产里可把 Planner / Critic 换成 LLM，**结构（Plan、Trace、Decision、FSM）保持不变**。

## 6. 成功演示长什么样

```text
目标：调研向量数据库选型
计划：
  S1 澄清调研边界
  S2 检索候选方案
  S3 对比分析
  S4 输出选型建议
执行：
  S1 done · clarify_goal · …
  S2 done · search_notes · …
  S3 done · analyze_findings · …
  S4 done · write_deliverable · …
状态：idle → planning → executing → reflecting → done
交付：…（含候选与建议的摘要）
```

## 7. 常见坑

| 坑 | 修好 |
|----|------|
| 只测内存里「跑过一次」 | 报告必须打印 plan + 每步 observation |
| 失败后直接 abort | 周挑战要练习 retry 环 |
| 状态路径手写硬编码 | 由真实 `send(event)` 累积 |
| 把 LLM 接进来「更真」 | 今日禁止；先稳住结构 |

## 8. 与明日衔接

Week 15 进入多智能体：何时该拆成 Researcher / Writer，而不是一条管线里塞所有职责。  
今天先把**单 Agent 多步闭环**跑稳。
