# Day 54 笔记｜流式事件与工具状态（产品化信号）

## 1. 今天学什么？

Week 11 你已经会：选型 → 迷你框架 → 加业务工具。  
今天补产品侧最缺的一块：**实时事件**，让前端聊天窗能显示「正在调用工具…」。

| Day 49 Trace | Day 54 Stream |
|--------------|---------------|
| 跑完后回放 Thought/Action/Obs | 跑的过程中持续推送事件 |
| 服务调试、评测、审计 | 用户可见的加载态 / 工具卡片 |
| 整段 JSON / Markdown | `tool_start` / `tool_end` 增量信号 |

两者都要；今天练的是 **Stream**。

## 2. 前端迁移直觉

| 你熟悉的前端 | Agent 流式事件 |
|--------------|----------------|
| `fetch` 的 loading / success / error | 单次工具的 `running` / `ok` / `error` |
| SSE / WebSocket 推送 | `on_event` 回调（或将来的 SSE） |
| Redux action：`TOOL_START` / `TOOL_END` | `AgentEvent(type=...)` |
| 由 action 推导 UI state，不反向写死 | `derive_tool_statuses(events)` |

结论：把 Agent Loop 当成「后台任务」；**事件是给 UI 的协议**，最终文本只是其中一个 payload。

## 3. 最小事件协议

今天约定这些 `type`（字符串常量）：

```text
run_start   → 一次 run 开始（带 goal）
thought     → 模型本步文字（可有可无）
tool_start  → 即将执行某工具（name + call_id + args）
tool_end    → 工具结束（name + call_id + status + content）
final       → 最终回答
run_end     → 整次 run 结束（stopped_reason）
```

**硬规则**：每一个 `tool_start` 必须有且仅有一个对应 `tool_end`（同 `call_id`）。

## 4. 工具状态如何派生？

不要在业务里到处 `isLoading=True`。  
正确做法：

```text
事件流
  → derive_tool_statuses
  → [{call_id, name, status: pending|running|ok|error, content?}, ...]
  → 前端渲染工具卡片
```

映射建议：

| 事件 | 该 call 的 status |
|------|-------------------|
| 刚 `tool_start` | `running` |
| `tool_end` 且内容非 ERROR | `ok` |
| `tool_end` 且 `ERROR:` 前缀 | `error` |

## 5. 和框架 Runner 的关系

Day 52/53 的 `AgentRunner` 只返回最终 `AgentRunResult`——对 CLI Demo 够用，对产品不够。

今天做法（教学版）：

```text
StreamingRunner
  · 内部仍是 while Loop（语义同 AgentRunner）
  · 每执行一个工具：先 emit tool_start，再 execute，再 emit tool_end
  · 可选 on_event 回调（模拟推给前端）
  · 同时收集 events，便于单测与时间线渲染
```

**不改** `mini_framework.AgentRunner` 内核；产品化能力用包装层加，而不是把 UI 逻辑塞进 Loop。

## 6. 真实产品里还会多什么？

| 教学版（今天） | 生产常补 |
|----------------|----------|
| 同步 `on_event` | SSE / WebSocket |
| 整段 thought | token 级 `delta` |
| 假时钟 / 无耗时 | `duration_ms` |
| ScriptedChat | 真模型流式 API |

先把成对事件做对，再谈 token 流。

## 7. 常见坑

| 坑 | 症状 | 纠正 |
|----|------|------|
| 只 emit `tool_end` | UI 永远看不到「开始」 | 成对发送 |
| `tool_end` 忘带 `call_id` | 多工具时关错卡片 | 始终带同一 id |
| 用 print 字符串当协议 | 前端无法解析 | 结构化 `AgentEvent` |
| 把 Trace 整段当 Stream | 用户要等跑完才看见 | 边跑边推 |

## 8. 今日一句话

> 没有 `tool_start`/`tool_end`，Agent 产品只是「黑盒聊天」；有了事件，才像可交互的工作流。

## 9. 明日预告

Day 55（周挑战）：手写 Agent vs 框架版对比报告——把 Week 10–11 认知沉淀成一页文档。

---

## 我的记录（请自己填写）

1. 我认为前端最少要订阅的两种事件：  
2. 若一次 step 调两个工具，事件顺序应是：  
3. 我会用哪个字段把 start/end 配对：  
