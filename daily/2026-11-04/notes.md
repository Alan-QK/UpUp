# Day 66 笔记｜任务分解 Planner

## 1. 一句话定位

**Planner**：把「我想要 X」变成「按什么顺序做哪些可验收的小步」——**只规划，不执行**。

## 2. 为什么前端背景也需要这招

长任务直接甩给模型，常见翻车：

| 症状 | 根因 |
|------|------|
| 漏步骤 | 没有显式清单 |
| 顺序乱 | 依赖没声明 |
| 无法暂停/重试 | 没有步骤粒度状态 |
| 成本失控 | 不知道还要几步 |

前端类比：

| 你熟悉的 | Agent 侧 |
|----------|----------|
| 用户故事 → 任务拆解 | goal → Plan |
| 看板列：Todo / Doing / Done | step 状态（明日执行器） |
| 路由守卫 / 依赖加载 | `depends_on` |
| Feature flag 策略名 | `strategy` 字段（可观测） |

## 3. 最小数据结构

```text
Plan
├─ goal: "调研向量数据库选型"
├─ goal_kind: research
├─ strategy: heuristic:research
├─ complexity: medium
└─ steps:
   ├─ S1 clarify   depends=[]
   ├─ S2 research  depends=[S1]
   ├─ S3 analyze   depends=[S2]
   └─ ...
```

要点：

- **id 稳定**：执行器、日志、HITL 都靠 id 引用
- **depends_on 显式**：今天先做串行；以后可做有向无环图（DAG）
- **kind 可枚举**：clarify / research / design / execute / analyze / verify / deliver

## 4. 今日做法：启发式模板（不是偷懒）

```text
goal
  │ normalize（空白压缩）
  │ classify（coding > writing > ops > research > generic）
  │ 选模板骨架
  │ 短目标 → 最多 3 步；否则按 max_steps 截断
  ▼
Plan（可 render 成 Markdown）
```

为什么先模板？

1. **可测**：分类与步数断言稳定，不依赖模型抽风
2. **接口先行**：明天换 LLM，只要仍返回 `Plan`
3. **可观测**：`strategy=heuristic:coding` 一眼看出规划器版本

生产路径：`plan_from_goal` 内部改为「提示词 + 结构化输出校验」，外层签名不变。

## 5. 与记忆系统的关系（接 Week 13）

- 记忆回答「关于用户我已知什么」
- 规划回答「这件事怎么拆」
- 二者正交：复杂助理往往是 **召回偏好 → 规划步骤 → 执行工具**

## 6. 常见坑

1. **把最终答案写进 Plan**：Planner 输出步骤，不是调研结论
2. **步骤过大**：「完成整个项目」不是一步；要能单独验收
3. **隐式依赖**：只靠数组顺序、不写 `depends_on`，并行化时必炸
4. **不过滤垃圾目标**：空串 / `hi` 应早失败，别生成假计划

## 7. 明日预告

Day 67｜**Plan-and-Execute**：吃进今日的 `Plan`，逐步调用工具并回写结果。
