# Day 69 笔记｜状态机视角看 Agent

## 1. 一句话定位

把 Agent 从「一堆 if-else」收成 **有限状态机（FSM）**：当前在哪个阶段、收到什么事件、只能跳到哪些下一状态——写清楚，才不容易跑飞。

## 2. 为什么昨天的 Reflection 还不够

| 只有函数调用链 | 状态机视角 |
|----------------|------------|
| Plan → Execute → Reflect 散落在调用栈 | 每个阶段是显式状态 |
| 重试/改计划靠局部 `if` | 决策变成 **事件**，驱动转移 |
| HITL 难插 | `awaiting_hitl` 是一等公民状态 |
| 难画、难测、难演示 | 转移表可渲染成图，可单测非法跳转 |

前端类比：

| 你熟悉的 | Agent 侧 |
|----------|----------|
| XState / 状态机组件 | Agent FSM |
| Redux action → reducer | event → transition |
| loading / success / error | planning / done / aborted |
| 路由守卫 | 非法转移直接拒绝 |
| 审批流「待审核」 | `awaiting_hitl` |

## 3. 今日最小状态集（必须记住）

```text
idle            空闲，等目标
planning        分解任务（Planner）
executing       逐步执行（Executor）
reflecting      评审轨迹（Critic）
awaiting_hitl   等人确认（Human-in-the-loop）
done            成功结束
aborted         中止结束
```

主路径：

```text
idle --goal_received--> planning --plan_ready--> executing
  --execution_finished--> reflecting --decision_accept--> done
```

纠错环：

```text
reflecting --decision_retry--> executing
reflecting --decision_revise--> planning
reflecting --decision_abort--> aborted
```

人审：

```text
planning|executing|reflecting --need_hitl--> awaiting_hitl
awaiting_hitl --hitl_approved--> （回到挂起前预定的下一状态）
awaiting_hitl --hitl_rejected--> aborted
```

## 4. 事件 ≠ 状态

- **状态**：系统「现在在哪」（名词/进行时）
- **事件**：发生了什么、触发跳转（动词/过去式或命令）

Day 68 的四态决策，今天映射为事件：

| Reflection 决策 | FSM 事件 | 典型下一状态 |
|-----------------|----------|--------------|
| accept | `decision_accept` | `done`（或先 HITL） |
| retry | `decision_retry` | `executing` |
| revise | `decision_revise` | `planning` |
| abort | `decision_abort` | `aborted` |

## 5. 转移表比硬编码 if 更好

```text
(source_state, event) → target_state
```

好处：

1. **可枚举**：漏边、死边一眼看出  
2. **可测试**：断言「reflecting + decision_retry → executing」  
3. **可画图**：直接生成 Mermaid `stateDiagram`  
4. **可扩展**：加 HITL / 预算熔断只需加行，不改散落 if

非法转移（如表中不存在）应 **显式失败**，而不是默默停在原地——调试时更像前端路由 404。

## 6. 今日练习在练什么

不是画 PPT，而是用代码：

1. 定义状态 / 事件常量与默认转移表  
2. 实现 `AgentStateMachine.send(event)`（含 HITL 挂起与恢复）  
3. 把 Reflection 决策映射成事件并跑几条情景轨迹  
4. `render_mermaid` **画出** Agent 状态图  
5. 输出带固定二级标题的学习报告

## 7. 常见坑

1. **状态过多**：先 7 个核心态够用；工具内部细节别升成全局状态  
2. **事件当状态**：不要出现 `retrying` 同时又有 `decision_retry` 事件叠床架屋  
3. **HITL 丢上下文**：进入 `awaiting_hitl` 时要记住批准后回哪（`hitl_resume`）  
4. **允许任意跳转**：没有表约束的「状态」只是变量改名，不是状态机  
5. **图与表不一致**：Mermaid 必须由同一份 `default_transitions()` 生成

## 8. 明日预告

Day 70｜**周挑战：多步研究任务**——把 Planner + Executor + Reflection + 今日状态机串成可展示的研究闭环。
