# Day 43 笔记｜单轮 Tool Call 执行

## 1. 今天学什么？

Day 42 写好了工具契约（模型「能看见什么」）。今天做下一步：模型一旦返回 `tool_calls`，本地代码如何 **解析并真正执行**。

```text
用户提问
  → 模型（带 tools[]）决定调用哪个工具
    → assistant 消息里出现 tool_calls[]
      →【今天】执行器：解析 arguments → 调本地函数 → 产出 tool 消息
        →（明天 D44）把 tool 结果塞回 messages，再问模型
```

前端类比：

| 前端 | 今天 |
|------|------|
| 按钮 `onClick` 只声明意图 | `tool_calls` 只声明「想调什么」 |
| 事件处理函数真正改状态 / 打 API | 执行器真正跑本地函数 |
| 错误边界把异常变成 UI 文案 | 失败也要变成可读的 `content` 字符串 |

## 2. 模型返回的 `tool_calls` 长什么样？

Chat Completions 里，助手若要调工具，大致是：

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    {
      "id": "call_abc123",
      "type": "function",
      "function": {
        "name": "get_weather",
        "arguments": "{\"city\": \"Shanghai\", \"unit\": \"celsius\"}"
      }
    }
  ]
}
```

注意：

- `arguments` 是 **JSON 字符串**，不是已经解析好的对象
- 一次响应里可能有 **多个** `tool_calls`（并行调用意图）
- `id` 后面回填 `role=tool` 时必须原样带上（`tool_call_id`）

## 3. 执行器要做的五步

1. **取出** `message["tool_calls"]`（没有就当作空列表）
2. **解析** 每一条：校验 `id` / `type` / `function.name` / `function.arguments`
3. **JSON.parse** `arguments` → `dict`（失败要变成可回传的错误，不要让进程炸掉）
4. **路由**：用 `name` 查注册表（registry）拿到可调用对象
5. **执行 + 字符串化**：成功把返回值变成字符串；异常捕获后写成失败文案

今日练习把这些步骤拆成可测函数：`parse_tool_call` → `execute_tool_call` → `execute_assistant_tool_calls` → `to_tool_messages`。

## 4. 回填消息格式（为明天铺路）

执行完一条工具后，要产出：

```json
{
  "role": "tool",
  "tool_call_id": "call_abc123",
  "content": "{\"city\": \"Shanghai\", \"temp_c\": 28, \"condition\": \"sunny\"}"
}
```

约定（今日练习）：

- 成功：`content` 尽量是 JSON 文本（或纯数字字符串），方便模型继续读
- 失败：`content` 以 `ERROR:` 开头，写清原因（未知工具 / 参数非法 / 执行异常）
- **即使失败也要回 `role=tool`**：让模型有机会改参数或换说法，而不是对话链断裂

## 5. 今日三个本地工具（与 Day 42 对齐）

| 工具 | 行为（练习用 mock） |
|------|---------------------|
| `get_weather` | 按城市返回固定天气 dict（不打真实 API） |
| `calculate` | 安全求值算术表达式（只允许数字与 `+ - * / // % ** ()`） |
| `get_current_time` | 返回固定演示时间字符串（可带 timezone 字段） |

真实项目里你会换成 HTTP / DB / 文件系统；协议层不变。

## 6. 安全意识（现在就要有）

- **不要**对模型给的表达式直接 `eval`
- **不要**按模型给的名字动态 `import` / 调任意属性
- 注册表是 **白名单**：只有你显式注册的工具才能跑
- 参数先校验类型与必填，再进业务函数

## 7. 和「完整 Agent」的差别

| | 今天（单轮执行） | 完整 Agent Loop |
|--|------------------|-----------------|
| 输入 | 已有 `tool_calls` | 用户目标 + 多轮决策 |
| 动作 | 执行一次工具 | 思考 → 行动 → 观察 → 再决策 |
| 输出 | `role=tool` 消息 | 最终自然语言回答或更多 tool_calls |

先把执行器做对，后面写 Loop 才不会把「调工具」和「说话」搅在一起。

## 8. 今日一句话

> Tool Call 是模型的「意图票据」；执行器负责兑现票据，并把收据（tool 消息）交还给对话。

## 9. 明日预告

Day 44：工具结果回填多轮——把今天的 `role=tool` 拼进 messages，再请求模型生成最终回答。

---

## 我的记录（请自己填写）
