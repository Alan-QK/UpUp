# Day 67 笔记｜Plan-and-Execute

## 1. 一句话定位

**Plan-and-Execute**：先拿到结构化 `Plan`，再按 `depends_on` **逐步调用工具**，把每步观察写进共享状态——**规划与执行分离**。

## 2. 为什么昨天的 Planner 不够

| 只有 Plan | Plan + Execute |
|-----------|----------------|
| 知道「该做什么」 | 真的去做并留下证据 |
| 无法暂停/重试单步 | 每步有 `done/failed/skipped` |
| 无法对接工具 | `kind → tool` 可替换 |
| 难做 HITL | 可在某 step_id 卡住等人确认 |

前端类比：

| 你熟悉的 | Agent 侧 |
|----------|----------|
| 路由表 + 懒加载 | Plan steps + 按需调工具 |
| Redux / 看板状态 | `ExecutionState.results` |
| 共享 Context / 黑板 | `context` dict |
| Promise 链 / 依赖数组 | `depends_on` |

## 3. 最小执行循环

```text
Plan.steps（有序）
  │
  ├─ deps 未全部 DONE？ → SKIPPED（可 stop=blocked）
  ├─ 映射 kind → tool_name（可 overrides）
  ├─ invoke(tool, step, context)
  │     ├─ 成功 → DONE + observation 写入 results / context
  │     └─ 异常 → FAILED + error；可 stop=failed
  └─ 超 max_steps？ → 停止，其余 SKIPPED
```

要点：

- **今日不做并行调度**：按数组顺序扫；DAG 并行是进阶
- **FAILED 的依赖不算满足**：下游必须跳过或重规划（明日 Reflection）
- **context 是黑板**：`search_notes` 写入的 `notes`，供 `analyze_findings` 读取

## 4. 工具映射（可观测）

```text
clarify  → clarify_goal
research → search_notes
design   → draft_outline
execute  → run_action
analyze  → analyze_findings
verify   → verify_checklist
deliver  → write_deliverable
```

生产里：工具换成真实 HTTP / DB / 浏览器；**执行器骨架不变**。

## 5. 与 ReAct 的差别（概念）

| ReAct | Plan-and-Execute |
|-------|------------------|
| 边想边做，每步让模型选动作 | 先定计划再执行 |
| 灵活，易跑偏 | 可控，易审计 |
| 适合探索 | 适合流程清晰的长任务 |

很多系统两者混用：粗计划 + 步骤内 ReAct。

## 6. 常见坑

1. **把依赖当成「数组下标」**：必须读 `depends_on`，否则以后并行必炸
2. **失败后仍执行下游**：污染 context；默认 `stop_on_failure=True`
3. **max_steps 把 skip 也算进去**：限额应约束「贵的工具调用」
4. **工具直接 print 当结果**：要返回 `str` observation，便于轨迹回放

## 7. 明日预告

Day 68｜**Reflection**：对 FAILED / 低质量观察做 critic，决定重试、改计划或接受。
