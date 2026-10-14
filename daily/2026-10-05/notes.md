# Day 52 笔记｜框架重写手写 Agent（对照理解）

## 1. 今天学什么？

Week 10 你已经手写过完整 Loop。Day 51 定了「少而精」的选型原则。  
今天做一件事：**用框架风格的 API，重写同一套能力**，看清抽象落在何处。

| 不要做 | 要做 |
|--------|------|
| 第一天就啃真实 LangChain 文档海洋 | 先用迷你框架把概念钉死 |
| 换一套全新业务 | **同能力**：lookup + calculate + max_steps |
| 背 API 名字 | 能画出 **手写 ↔ 框架** 映射 |

## 2. 前端迁移直觉

| 你熟悉的前端 | 今天的 Agent 框架层 |
|--------------|---------------------|
| 自己写过一遍 `useReducer` | Day46 手写 `run_agent_loop` |
| 再上 Zustand / Redux Toolkit | 今天的 `AgentRunner` + `ToolRegistry` |
| `createSlice` / middleware | Tool 装饰器、中间层封装 |
| 组件 props 约定 | Agent 配置（tools / max_steps / system） |

结论：框架不是新算法，是**工程约定 + 样板代码收纳**。

## 3. 概念对照表（练习会编码）

| 手写（Day46） | 迷你框架（今天） | 真实框架里常见叫法 |
|---------------|------------------|--------------------|
| `tools.py` 里的 schema + handler | `Tool` + `ToolRegistry` | `@tool` / ToolNode / function tools |
| `execute_assistant_tools` | `registry.execute_assistant_tools` | ToolExecutor / tool calling runtime |
| `run_agent_loop(...)` | `AgentRunner.run(agent, goal, chat)` | AgentExecutor / Runner / graph.invoke |
| `messages: list[dict]` | `AgentState.messages` | State / MemorySaver 里的 messages |
| `LoopResult` | `AgentRunResult` | RunResult / AgentResponse |
| `max_steps` | `FrameworkAgent.max_steps` | recursion_limit / max_turns |
| `ScriptedChat` | 同一个 `chat` 回调 | ChatModel / LLM 适配器 |

背这张表，比背某个库的 import 路径更保值。

## 4. 迷你框架长什么样？（心智模型）

```text
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ FrameworkAgent │──▶│ AgentRunner  │──▶│ AgentRunResult│
│ tools/max_steps│   │  while Loop  │     │ final/stop   │
└──────┬──────┘     └──────┬───────┘     └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     chat(messages)
│ ToolRegistry│◀──── tool_calls → Observation
└─────────────┘
```

Runner 内部伪代码（和 Day46 几乎一样）：

```python
state = AgentState(messages=[system, user(goal)])
for step in range(1, agent.max_steps + 1):
    assistant = chat(state.messages)
    state.messages.append(assistant)
    if not has_tool_calls(assistant):
        return final_answer
    obs = registry.execute(assistant)
    state.messages.extend(obs)
return stopped_max_steps
```

**差别**：工具从「散落函数」变成「注册表对象」；Loop 从「自由函数」变成「Runner 方法」。

## 5. 为什么今天不装真框架？

1. **对照优先**：真框架文档会把 RAG、Chain、Callback、LCEL 一起砸过来
2. **可测可控**：`ScriptedChat` + 标准库，CI 零密钥
3. **下周接真货时有锚点**：Day53+ 扩展工具、Day55 写对比报告时，你知道该比什么

今天的 `mini_framework.py` = 教学用「假框架」，API 刻意像常见 SDK，但实现你自己写完。

## 6. 同能力验收（与 Day46 对齐）

目标示例：「查 `alpha` 的值，再把它乘以 3」

1. Action: `lookup(key=alpha)` → `7`
2. Action: `calculate(expression=7*3)` → `21`
3. Final：说明结果是 21

若框架版跑不通、手写版能跑——说明你丢了某段映射（通常是 Observation 回填或 stop 条件）。

## 7. 常见坑

| 坑 | 症状 | 纠正 |
|----|------|------|
| 把框架当魔法 | 说不清谁在调工具 | 打开 Runner，指到 `while` |
| Registry 不校验未知工具 | 任意 name 直接炸 | 未知 → `ERROR:` 观察回填 |
| 忘了 deepcopy messages | 测试里串状态 | 入参 / 出参都拷贝 |
| 急着装 LangGraph | 概念和报错缠在一起 | 先完成本课对照 |

## 8. 今日一句话

> 框架重写的价值不在「跑得更酷」，而在「你终于看懂框架在替你写哪一段 while」。

## 9. 明日预告

Day 53：自定义工具接入框架——在 Registry 上新增 1 个业务工具，体验扩展点。

---

## 我的记录（请自己填写）

1. 我最容易混淆的一对概念（手写 ↔ 框架）：  
2. Runner 里我改动最多的一段逻辑：  
3. 若换成真框架，我准备先对照哪三行 API：  
