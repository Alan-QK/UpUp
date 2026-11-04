# Day 46 笔记｜ReAct 与 Agent Loop

## 1. 为什么需要 Loop？

Day 45 的双工具 Agent 本质是：

```text
问一次模型 →（可选）执行工具 → 再问一次 → 结束
```

真实任务经常是：**第一次工具结果不够**，模型还要再查、再算、再确认。  
于是编排从「固定两跳」变成：

```text
while True:
    模型思考并决定行动
    若给出最终答案 → break
    否则执行工具，把观察塞回对话，继续
```

这就是 **Agent Loop**。ReAct 是给这个循环起的经典名字与写法。

## 2. ReAct 四个词（对照现代协议）

论文里常见文本格式：

```text
Thought: 我需要先查法国首都
Action: lookup("france_capital")
Observation: Paris
Thought: 知道首都了，可以回答
Final Answer: 法国首都是 Paris
```

你在 API 里通常**不会**真的解析这套纯文本（脆弱），而是用 Tool Calling：

| ReAct 概念 | 现代消息里长什么样 |
|------------|-------------------|
| Thought | `assistant.content`（可空；有的模型把推理藏在别处） |
| Action | `assistant.tool_calls[]` |
| Observation | `role=tool` + `tool_call_id` |
| Final Answer | `assistant` **没有** `tool_calls`，只有自然语言 `content` |

**心智用 ReAct，实现用 Tool Calling。** 今天练习走后者。

## 3. 最小伪代码（请背下来）

```python
messages = [system, user(goal)]
for step in range(1, max_steps + 1):
    assistant = chat(messages)
    messages.append(assistant)
    if not has_tool_calls(assistant):
        return final_answer
    tool_msgs = execute(assistant)   # 白名单执行
    messages.extend(tool_msgs)       # Observation 回填
return stopped_because_max_steps
```

和 Day 44/45 的差别只有一点：**把「再问一次」放进循环**，允许多轮 Action。

前端类比：不是点一次按钮就结束，而是「加载 → 根据结果再请求」的轮询状态机，直到 `status=done` 或超时。

## 4. 今天的两个小工具

| 工具 | 作用 | 为什么适合练 Loop |
|------|------|-------------------|
| `lookup` | 查本地知识表 | 第一步拿事实 |
| `calculate` | AST 安全计算器 | 第二步基于观察再算 |

多步样例目标：

> 「查 `alpha` 的值，再把它乘以 3」

1. Action: `lookup(key=alpha)` → Observation: `7`  
2. Action: `calculate(expression=7*3)` → Observation: `21`  
3. Final Answer: 说明结果是 21  

一步查不到答案 → 必须再绕一圈，这就是 Loop 存在的意义。

## 5. `stopped_reason` 两种正常结局

| 值 | 含义 |
|----|------|
| `final_answer` | 某次 `chat()` 返回的 assistant **没有** tool_calls |
| `max_steps` | 已经跑满 `max_steps` 次模型调用，仍未给出最终回答（或最后一轮仍在要工具） |

今天只要让这两种出路都**可测、不崩**。更细的 stop 规则（连续重复调用、强制收尾文案等）→ Day 47。

## 6. 和框架的关系（先别急）

LangGraph / Agents SDK 内部也是类似循环 + 状态图。  
你先手写 while，下周用框架重写同能力时，才会看懂「节点 / 边」在抽象什么。

## 7. 安全提醒（Loop 放大风险）

- 步数越多，费用与延迟线性涨 → **必须** `max_steps`
- 工具仍要白名单；计算器继续禁 `eval`
- 失败观察也要回填（`ERROR: ...`），让模型有机会改，而不是直接炸进程（Day 48 会专门练）

## 8. 今日一句话

> Agent = LLM + Tools + **Loop**；ReAct 是给 Loop 的思考方式，不是另一个产品名。

## 9. 明日预告

Day 47：终止条件与步数限制——把「何时停」设计成可配置规则，彻底防死循环。

---

## 我的记录（请自己填写）
