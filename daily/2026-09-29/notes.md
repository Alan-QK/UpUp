# Day 48 笔记｜工具错误恢复

## 1. Day 47 停得住，今天要「错了还能走」

昨天学会了：

| 信号 | 含义 |
|------|------|
| `final_answer` | 正常收尾 |
| `max_steps` / `last_step_tools` | 预算用尽 |
| `repeated_action` | 同一动作指纹连打 |

还缺一块：**工具调用本身失败**时怎么办？

前端直觉：

- 表单提交 400 → 展示字段错误，让用户改，而不是整站 500
- Agent 同理：工具 `ERROR:` → 回填观察 → 模型改参数再试

## 2. 三种常见工具失败（今天都会练到）

| 类型 | 例子 | 工具层行为 |
|------|------|------------|
| 缺字段 | `calculate` 没传 `expression` | `ERROR: missing expression` |
| 业务拒绝 | `lookup("gamma")` 不在知识表 | `ERROR: unknown key: gamma` |
| 协议损坏 | `arguments` 不是合法 JSON | `ERROR: arguments must be valid JSON` |

`tools.execute_one` **已经**把异常吞掉并写成 `role=tool` 消息。  
你今天的主战场是：**Loop 如何识别 ERROR、允许纠正、并限制连续失败**。

## 3. 为什么不能 `raise` 打断 Loop？

```text
坏：execute() 抛异常 → 整个 Agent 进程崩 → 用户看到白屏/500
好：execute() 返回 ERROR: ... → messages 里多一条 tool 观察 → 模型下一轮自己改
```

协议层（OpenAI 兼容 Tool Calling）本来就假设：  
**每一次 tool call 都有一条 tool 消息回来**——成功是 JSON 结果，失败也可以是可读错误文本。

## 4. RecoveryPolicy

| 字段 | 默认 | 作用 |
|------|------|------|
| `max_steps` | 6 | 最多调用模型多少次 |
| `max_consecutive_errors` | 3 | 连续「含 ERROR 的 action 步」达到该值即停 |

注意：

- 一次 step 里只要有一条观察是 `ERROR:`，整步记为 `error_action`
- 下一步若全部成功（或直接 final），计一次 **recovery**
- 连续 `error_action` 触顶 → `too_many_errors`（和 Day 47 的「同指纹重复」不同）

## 5. recovery_count 怎么数

```text
consecutive_errors = 当前连续 error 步数

遇到 error_action:
  consecutive += 1

遇到成功 action（err_count==0）且 consecutive>0:
  recovery_count += 1；consecutive = 0

遇到 final 且仍处 consecutive>0:
  recovery_count += 1   # 错误后直接收尾，也算一次闭环
  （若已在成功 action 清过零，final 不再重复计数）
```

## 6. 伪代码（对照练习）

```python
policy = RecoveryPolicy(...)
consecutive = 0
recovery = 0

for index in 1..policy.max_steps:
    assistant = chat(messages)
    messages.append(assistant)

    if not has_tool_calls(assistant):
        if consecutive > 0:
            recovery += 1
        return final_answer

    obs = execute(assistant)   # 失败也是 ERROR: 字符串，不抛
    messages.extend(obs)

    if any_error(obs):
        consecutive += 1
        kind = "error_action"
    else:
        if consecutive > 0:
            recovery += 1
        consecutive = 0
        kind = "action"

    if consecutive >= policy.max_consecutive_errors:
        return too_many_errors

return max_steps
```

## 7. 和 Day 47 / Day 49 的分工

| Day | 管什么 |
|-----|--------|
| 47 | **何时停**（预算、重复动作） |
| **48** | **错了怎么继续**（ERROR 回填 + 纠正 + 连续失败上限） |
| 49 | **怎么看清过程**（完整 Trace / 回放） |

生产 Agent 通常三者都要：停得住、错得起、看得见。

## 8. 前端迁移一问

若在对话 UI 展示工具状态：

- `error_action` → 红色「工具失败：missing expression」
- 下一轮成功 → 绿色「已纠正并重试」
- `too_many_errors` → 明确提示「多次失败，请换种问法或人工介入」

这比只显示「思考中…」对用户诚实得多。

## 9. 今日一句话

> 工具失败不是事故终点，而是下一轮 Thought 的输入。

## 10. 明日预告

Day 49：轨迹日志 Trace——把每步 action / observation 打成可回放记录。

---

## 我的记录（请自己填写）
