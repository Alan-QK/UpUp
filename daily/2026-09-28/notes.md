# Day 47 笔记｜终止条件与步数限制

## 1. Day 46 留下的坑

昨日最小 Loop 只有两种出路：

| 原因 | 含义 |
|------|------|
| `final_answer` | 模型不再带 `tool_calls` |
| `max_steps` | 跑满预算仍在要工具 |

这在 Demo 够用，上线不够：

1. **模型卡死**：一直 `lookup(alpha)` → `lookup(alpha)` → … 烧满步数才停，太晚
2. **最后一步还执行工具**：明明已经没机会再问模型，却多付一次工具成本
3. **策略散落在 if 里**：没法单测、没法按任务调参

今天把「何时停」抽成 **StopPolicy**。

## 2. 三种该停的信号（背下来）

```text
① 正常收尾     无 tool_calls → final_answer
② 步数预算    触顶 / 最后一步仍要工具 → max_steps 或 last_step_tools
③ 行为异常    连续相同 Action 指纹 → repeated_action
```

前端类比：请求重试要有 **maxRetries**；同一失败错误连打要 **circuit breaker**；最后一次重试后就别再发写请求。

## 3. Action 指纹（fingerprint）

只比「工具名」不够：`lookup(alpha)` 与 `lookup(beta)` 是不同动作。

指纹建议：

```text
name + ":" + canonical_json(arguments)
```

多条 tool_calls 时，按顺序用 `|` 拼接。  
参数 dict 用 `sort_keys=True` 的紧凑 JSON，避免键序导致误判「不同」。

连续两次（或 N 次）指纹完全相同 → 判定卡住 → `repeated_action`。

## 4. StopPolicy 字段

| 字段 | 默认 | 作用 |
|------|------|------|
| `max_steps` | 6 | 最多调用模型多少次 |
| `max_identical_streak` | 2 | 连续相同指纹达到该值即熔断 |
| `block_tools_on_last_step` | True | 最后一步若仍要工具：**不执行**，直接停 |

校验提醒：Python 里 `bool` 是 `int` 子类，`True` 不能当 `1` 用。

## 5. 最后一步拦截（为什么重要）

`max_steps=3` 且模型第三轮仍带 tool_calls：

| 策略 | 行为 | 代价 |
|------|------|------|
| Day 46 风格 | 执行工具 → 然后因循环结束而停 | 白跑工具，且没有下一轮模型消化观察 |
| 今日 `block_tools_on_last_step` | **不执行** → `last_step_tools` | 省工具；明确告诉调用方「预算不够了」 |

生产里还可以再加：最后一步强制改写 system「禁止工具、必须作答」——那是 Prompt 层技巧，今天先把编排层做对。

## 6. 伪代码（对照练习）

```python
policy = StopPolicy(...)
streak = 0
last_fp = None

for index in 1..policy.max_steps:
    assistant = chat(messages)
    messages.append(assistant)

    if not has_tool_calls(assistant):
        return final_answer

    if index == policy.max_steps and policy.block_tools_on_last_step:
        return last_step_tools   # 不 execute

    obs = execute(assistant)
    messages.extend(obs)

    fp = fingerprint_tool_calls(assistant)
    streak = streak + 1 if fp == last_fp else 1
    last_fp = fp
    if streak >= policy.max_identical_streak:
        return repeated_action

return max_steps   # block_tools_on_last_step=False 时的收尾
```

## 7. 和后续课程的关系

| Day | 你会补上 |
|-----|----------|
| 48 | 工具 ERROR 时让模型纠正（失败恢复） |
| 49 | 更完整的 Trace / 回放 |
| 50 | 只读文件助手（权限边界） |

终止条件是 **安全与成本的第一道闸**；错误恢复是第二道。

## 8. 今日一句话

> Loop 能跑起来不算完；**能稳定停下来**才算工程。

## 9. 明日预告

Day 48：工具错误恢复——非法参数 / 未知工具时，把 `ERROR:` 观察回填并引导模型改正。

---

## 我的记录（请自己填写）
