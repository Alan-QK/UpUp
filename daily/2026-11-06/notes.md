# Day 68 笔记｜Reflection 反思纠错

## 1. 一句话定位

**Reflection**：在 Plan-and-Execute 之后，加一轮 **critic（评审）**——对失败 / 低质量观察打分，再决定 **接受、重试、改计划或中止**。

## 2. 为什么昨天的执行器不够

| 只有 Execute | Execute + Reflection |
|--------------|----------------------|
| 失败就停 | 能区分「偶发失败」vs「计划不行」 |
| 低质量观察也会 DONE | 对 observation 做质量门槛 |
| 轨迹只给人看 | critic 把轨迹变成可执行决策 |
| 难闭环 | 形成 Plan → Execute → Reflect →（再）Plan |

前端类比：

| 你熟悉的 | Agent 侧 |
|----------|----------|
| CI 失败后重跑 flaky 测试 | `retry` |
| Code Review 打回改设计 | `revise` |
| Lighthouse / 质量门禁 | score + issues |
| feature flag 熔断 | `abort` |

## 3. 四态决策（今天必须记住）

```text
accept  — 够用，收下结果
retry   — 同一步再试（换提示 / 换工具参数 / 清临时错误）
revise  — 计划本身有问题，交回 Planner
abort   — 重试耗尽或不可恢复，停止并上报
```

优先级（从高到低）：**abort > revise > retry > accept**。

含义：只要有一步需要改计划，就不能假装「再试一次」就完事；熔断优先于修补。

## 4. 最小反思循环

```text
RunSnapshot（执行轨迹）
  │
  ├─ 逐步 critique_step → score / issues / decision
  ├─ critique_run → 看 stop_reason、交付物
  ├─ pick_overall_decision（按优先级合并）
  │
  ├─ accept → 结束
  ├─ abort  → 结束
  ├─ revise → 结束（留给 Planner，今日不真改计划）
  └─ retry  → improve 最差一步 → 新 RunSnapshot → 下一轮
         （受 max_rounds 约束）
```

要点：

- **今日不调用 LLM**：用启发式打分，结构与「模型当 critic」相同
- **RETRY 只修一步**：每轮挑分数最低且可重试的步骤
- **SKIPPED 常指向 REVISE**：下游被上游拖死，盲着重试下游没用

## 5. 启发式打分（mock critic）

| 信号 | 倾向 |
|------|------|
| `status=failed` / 有 error | 低分 → retry（若还有轮次） |
| `status=skipped` | 低分 → revise（依赖/计划问题） |
| `done` 但观察为空 / 过短 | 中低分 → retry |
| `stop_reason=failed/blocked` 且多步 skipped | revise |
| 全 done + 有交付物 + 观察够长 | accept |

生产里把启发式换成「第二个模型 + 结构化输出」即可，**循环骨架不变**。

## 6. 常见坑

1. **无脑重试**：对 `skipped` 重试解决不了依赖；应 revise
2. **没有 max_rounds**：critic 与 actor 互怼会死循环
3. **把 revise 做成原地乱改 steps**：改计划应回到 Planner，保持职责分离
4. **只看 stop_reason**：有时 `completed` 但交付物空洞——仍要打 observation 质量分

## 7. 明日预告

Day 69｜**状态机视角**：把 Plan / Execute / Reflect / 人审 画成状态图，为复杂 Agent 建模打底。
