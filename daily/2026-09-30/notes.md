# Day 49 笔记｜轨迹日志 Trace

## 1. 为什么今天专门讲 Trace？

Week 10 前四天已经能：

| Day | 能力 |
|-----|------|
| 46 | 跑起来（ReAct Loop） |
| 47 | 停得住（预算 / 熔断） |
| 48 | 错得起（ERROR 回填） |

还缺一块：**事后看得清**。

生产 Agent 最贵的不是多调一次工具，而是「出了怪结果却不知道哪一步走歪了」。  
Trace 就是 Agent 的 **DevTools Timeline**：每一步 Thought / Action / Observation 可回放。

## 2. 前端迁移直觉

| 前端 | Agent Trace |
|------|-------------|
| Redux DevTools 逐步回放 | 逐步回放 Thought→Action→Obs |
| Performance 面板火焰图 | 步数、工具耗时、错误步 |
| `console.log` 临时调试 | **结构化事件**（可存盘、可评测） |
| Source Map 还原堆栈 | JSONL 还原整段对话决策链 |

别只 `print(messages)`——那是原始日志。  
今天要练的是：**规范化的一步一条记录**。

## 3. 一条好 Trace 长什么样

每一步至少包含：

```text
Step 1 · action
  Thought: 先查 alpha
  Action: lookup(key=alpha)
  Observation: {"key":"alpha","value":"7"}

Step 2 · final
  Thought: alpha 的值是 7。
```

要求：

- **可读**：人能一眼扫完
- **可序列化**：能写成 JSONL，明天还能加载
- **可回放**：加载后渲染出与当时一致的文本

## 4. 结构化 vs 纯字符串

```python
# 坏：只有一大段 markdown，难做自动化评测
trace_md = "# Step 1 ..."

# 好：先有结构，再按需渲染
TraceStep(index=1, kind="action", thought=..., actions=(...), observations=(...))
```

结构在前，展示在后——和前端「数据层 → 视图层」一样。

## 5. JSONL：一行一步

JSONL = 每行一个 JSON 对象。适合追加写：

```text
{"type":"meta","goal":"...","max_steps":6}
{"type":"step","index":1,"kind":"action",...}
{"type":"step","index":2,"kind":"final",...}
{"type":"end","stopped_reason":"final_answer","final_content":"..."}
```

好处：

- 边跑边 flush，进程崩了也不丢前面的步
- 评测脚本按行读即可，不必整文件 parse 成巨型数组

## 6. Live Print：边跑边看

调试时打开 `live_print=True`：每完成一步立刻把 `format_step_block` 打到 stdout。  
像前端 HMR 的「即时反馈」，而不是等整段 Loop 结束才 `cat` 日志。

注意：演示 / 单测里可以把输出接到 `io.StringIO`，避免污染 pytest 输出。

## 7. 伪代码（对照练习）

```python
policy = TracePolicy(max_steps=6, live_print=True)
messages = [system, user(goal)]
steps = []

for index in 1..policy.max_steps:
    assistant = chat(messages)
    messages.append(assistant)
    thought = assistant_thought(assistant)

    if not has_tool_calls(assistant):
        step = TraceStep(index, "final", thought, (), ())
        steps.append(step)
        maybe_print(step)
        return TraceLog(..., stopped="final_answer")

    obs_msgs = execute(assistant)
    messages.extend(obs_msgs)
    actions = extract_actions(assistant)
    observations = extract_observations(obs_msgs)
    step = TraceStep(index, "action", thought, actions, observations)
    steps.append(step)
    maybe_print(step)

return TraceLog(..., stopped="max_steps")
```

## 8. 和 Day 48 / Day 50 的分工

| Day | 管什么 |
|-----|--------|
| 48 | 错了怎么继续（恢复策略） |
| **49** | **过程怎么留下**（Trace / JSONL / 回放） |
| 50 | 周挑战：只读文件助手（权限边界） |

里程碑 `tool-agent` 验收项里明确要求：**有 trace 日志（每步可回放）**——今天就是在给这块打桩。

## 9. 今日一句话

> 没有 Trace 的 Agent，就像没有 DevTools 的前端——能跑，但不敢改。

## 10. 明日预告

Day 50：周挑战——只读文件助手（目录列举 + 读文件，权限最小化）。

---

## 我的记录（请自己填写）
