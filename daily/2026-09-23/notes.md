# Day 44 笔记｜工具结果回填多轮

## 1. 今天学什么？

Day 43 已经能把 `tool_calls` **兑现成** `role=tool` 收据。今天补上协议的下半段：把收据塞回对话，**再请求一次模型**，让它根据观察写出最终回答。

```text
messages = [system?, user, ...]
  → ① 模型返回 assistant + tool_calls
  → ② 本地执行器产出 role=tool（可多条）
  → ③ messages += assistant + tool*
  → ④ 再问模型 → assistant（最终自然语言，通常不再带 tool_calls）
```

前端类比：

| 前端 | 今天 |
|------|------|
| `dispatch(fetchStart)` | assistant 宣布要调工具 |
| `await api()` 得到 data | 执行器产出 tool.content |
| `dispatch(fetchSuccess)` 再渲染 | 把 tool 消息 append 后再聊一轮 |
| React Query 的 `onSuccess` 链式更新 | `run_tool_roundtrip` 编排 |

## 2. 正确的消息顺序（死记）

一轮工具调用结束后，发给模型的 messages 必须长这样：

```json
[
  {"role": "user", "content": "上海今天热不热？算一下 28*9/5+32"},
  {
    "role": "assistant",
    "content": null,
    "tool_calls": [
      {"id": "call_1", "type": "function", "function": {"name": "get_weather", "arguments": "..."}},
      {"id": "call_2", "type": "function", "function": {"name": "calculate", "arguments": "..."}}
    ]
  },
  {"role": "tool", "tool_call_id": "call_1", "content": "{\"temp\":28,...}"},
  {"role": "tool", "tool_call_id": "call_2", "content": "{\"result\":82.4}"},
  {"role": "assistant", "content": "上海约 28°C……换算约 82°F。"}
]
```

要点：

- **每条** `tool_calls[i].id` 都要有对应的 `tool` 消息
- 多个 tool 时，**顺序建议与 tool_calls 一致**（今日练习强制一致，减少歧义）
- 不要跳过 assistant 只塞 tool——模型需要看见「自己发过什么调用意图」

## 3. 校验什么？（`validate_tool_followup`）

今日练习要求：

1. assistant 必须带非空 `tool_calls` 列表
2. tool 消息条数 == tool_calls 条数
3. 第 i 条 tool 的 `tool_call_id` == 第 i 条 call 的 `id`（顺序锁定）
4. 每条 tool：`role == "tool"`，且 `content` 为 str（允许失败文案以 `ERROR:` 开头）

对不上就抛 `ValueError`，别把脏协议送给下一轮模型。

## 4. 为什么用注入的 `ChatFn`？

```python
ChatFn = Callable[[list[dict]], dict]  # 输入 messages，输出一条 assistant 消息
```

- 单测：塞 `ScriptedChat([first_with_tools, final_answer])`
- 真机：写成 `lambda msgs: openai_chat(msgs, tools=...)`
- 编排层不该关心 HTTP / SDK，只关心协议

`ScriptedChat` 会把每次收到的 messages **拷贝**进 `calls`，方便你断言「第二次请求已经带上 tool」。

## 5. `run_tool_roundtrip` 的两条路径

| 第一轮 assistant | 行为 |
|------------------|------|
| 无 `tool_calls` / 空列表 | 直接把 `content` 当最终回答；`tool_messages=[]` |
| 有 `tool_calls` | 执行 → 校验 → 拼接 → **再调一次** ChatFn；第二轮若仍带 tool_calls → 今日直接报错 |

今天**故意不做**多步循环（Day 46 的 ReAct Loop）。先把「回填再问」这一下做对。

## 6. 失败 tool 也要回填

若工具未知或参数非法，Day 43 约定 `content` 以 `ERROR:` 开头。今天仍然：

- **保留**那条 assistant（含失败意图）
- **照样** append `role=tool`
- 让第二轮模型有机会道歉、改口或换工具

删掉失败回合 = 对话失忆，模型会重复犯错。

## 7. 和完整 Agent Loop 的边界

| | 今天（一轮回填） | Day 46+ Agent Loop |
|--|------------------|--------------------|
| 工具回合数 | 最多 1 | 多步，直到停 |
| 终止 | 第二轮无 tool_calls | max_steps / 最终回答 / 用户取消 |
| 焦点 | 消息协议正确性 | 决策与防死循环 |

## 8. 今日一句话

> 工具结果不是日志，是对话的一部分：`tool_call_id` 对得上，模型才接得住。

## 9. 明日预告

Day 45 周挑战：把 Schema（D42）+ 执行器（D43）+ 回填（D44）拼成可演示的双工具 Agent Demo。

---

## 我的记录（请自己填写）
