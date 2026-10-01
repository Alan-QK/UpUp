# Day 45 笔记｜周挑战：双工具 Agent

## 1. 今天学什么？

Week 9 前四天拆开练过：

| Day | 积木 |
|-----|------|
| 42 | 工具 Schema（函数即契约） |
| 43 | 执行器（白名单 + 安全计算） |
| 44 | 回填协议（tool_call_id → 再问模型） |

今天把它们**焊成一台能演示的小机器**：只带两个工具——`calculate` 与 `get_current_time`。

```text
user 提问
  → ChatFn 决定要不要调工具（可并行两个）
  → 本地执行器兑现 tool_calls
  → 按协议回填 role=tool
  → 再问 ChatFn → 最终自然语言回答
```

前端类比：一个页面上两个副作用按钮（「算一下」「看时间」），点完把结果写回同一条会话时间线。

## 2. 为什么是「双工具」而不是越多越好？

周挑战的目标是 **最小可用（MVP）**：

- **边界清楚**：白名单只有 2 个名字，安全面可控
- **场景够用**：计算 = 确定性侧效应；时间 = 只读「环境事实」
- **可演示**：一句话就能同时触发两个 tool_calls（并行）

多工具、多步循环、权限分级——留给 Week 10。今天先把「一轮里调两个工具」做对。

## 3. `HeuristicChat`：练习专用的假模型

真实项目里 `ChatFn` 会打 HTTP。练习要零费用、可断言，所以提供启发式实现：

| 轮次 | 行为 |
|------|------|
| 第 1 次调用 | 读最后一条 user；`plan_tool_calls` → 有则带 `tool_calls`，无则直接最终回答 |
| 第 2 次调用 | 从 messages 里收集 `role=tool`，`synthesize_answer` 写成自然语言 |

签名与 Day 44 的 `ScriptedChat` 相同：`Callable[[list[dict]], dict]`。  
真机时：把 `HeuristicChat()` 换成 `lambda msgs: openai_chat(msgs, tools=dual_toolkit())` 即可。

## 4. 规划启发式（故意简单）

`plan_tool_calls` 不靠大模型，靠关键词 + 表达式抽取：

- 命中「算 / 计算 / + - * / …」→ 挂 `calculate`
- 命中「几点 / 时间 / 时区 / 现在 …」→ 挂 `get_current_time`
- 两者都命中 → **同一条** assistant 里放两个 tool_call（顺序：先时间后计算，或按题目约定）
- 都不命中 → 返回 `[]`，第一轮直接闲聊回答

这不是生产级 Router，只是让 Demo 离线可跑。生产用模型读 Schema 自己选工具。

## 5. 消息长什么样？（死记一遍）

用户：「现在 UTC 几点？再帮我算 3+4」

```json
[
  {"role": "system", "content": "...只允许 calculate 与 get_current_time..."},
  {"role": "user", "content": "现在 UTC 几点？再帮我算 3+4"},
  {
    "role": "assistant",
    "content": null,
    "tool_calls": [
      {"id": "call_time", "type": "function",
       "function": {"name": "get_current_time", "arguments": "{\"timezone\":\"UTC\"}"}},
      {"id": "call_calc", "type": "function",
       "function": {"name": "calculate", "arguments": "{\"expression\":\"3+4\"}"}}
    ]
  },
  {"role": "tool", "tool_call_id": "call_time", "content": "{\"timezone\":\"UTC\",\"datetime\":\"...\"}"},
  {"role": "tool", "tool_call_id": "call_calc", "content": "{\"expression\":\"3+4\",\"result\":7}"},
  {"role": "assistant", "content": "UTC 现在是 …；3+4=7。"}
]
```

## 6. `run_dual_agent` 做什么？

编排层很薄：

1. 拼 `history = [system, user]`
2. `chat = chat or HeuristicChat()`
3. `result = run_tool_roundtrip(history, chat, execute=execute_dual_tools)`
4. 包成 `AgentResult`（最终文本、用过哪些工具名、完整 messages）

**不要**在编排里手写 HTTP；**不要**在编排里 `eval` 表达式——那是 `toolkit` 的事。

## 7. 安全提醒（今天就要养成）

- 计算器必须走 AST 白名单（`toolkit.safe_calculate`），禁止 `eval`
- 时区只是字符串标签；练习用固定 `DEMO_TIME_UTC`，不调系统时钟也没关系（可测）
- 未知工具名 → `ERROR: ...` 回填，而不是抛崩进程

## 8. 和明天的边界

| | 今天 D45 | Day 46+ |
|--|---------|---------|
| 工具回合 | ≤ 1 | 多步循环 |
| 选工具 | 启发式 / Scripted | 模型 + ReAct |
| 终止 | 第二轮无 tool_calls | max_steps / 最终回答 |

## 9. 今日一句话

> 两个工具、一轮回填、一条可演示的时间线——这就是最小 Agent。

## 10. 明日预告

Day 46：ReAct 与 Agent Loop——把「至多一轮」升级成可多步的思考-行动循环。

---

## 我的记录（请自己填写）
