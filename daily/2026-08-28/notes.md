# Day 27 笔记｜校验失败重试

## 1. 今天学什么？

承接 Day 26：已经能 `validate` 并得到「字段路径 + 原因」。  
今天把失败变成**可自动修复**的闭环：

```text
初始 messages
  → LLM 生成 raw
    → extract + pydantic 校验
      → 成功：返回结构化对象
      → 失败：把 raw + 错误摘要追加进对话，再调 LLM（最多修 3 次）
        → 仍失败：标记 exhausted，把轨迹留下排查
```

前端类比：

| 前端 | 今天 |
|------|------|
| 表单校验红字 + 用户改完再提交 | ValidationError 摘要 + 模型再生成 |
| 最多弹 3 次「请修正」 | `max_repairs=3` |
| 保留错误请求日志 | `AttemptRecord` 轨迹 |

## 2. 为什么需要 repair，而不是直接炸？

结构化输出一次成功率通常不是 100%：

- 多写解释、包了 Markdown 围栏
- 枚举写错（`紧急` 而不是 `high`）
- 漏字段、类型不对

工程上常见策略：

1. **Prompt 里塞 Schema**（提高一次成功率，Day 26）
2. **校验失败自动 repair**（今天）
3. 厂商 Structured Outputs / tool_call 强制（后面会碰到）

Repair 是「与模型厂商无关」的通用保险丝。

## 3. 次数怎么数？

今日约定（请与测试对齐）：

| 名词 | 含义 |
|------|------|
| 首次生成 | 第 1 次调用 LLM（不算 repair） |
| 修复重试 | 校验失败后再调用；默认最多 **3** 次 |
| 总调用上限 | `1 + max_repairs`（默认 4） |

```text
attempt=1  首次 → 失败
attempt=2  repair #1 → 失败
attempt=3  repair #2 → 失败
attempt=4  repair #3 → 仍失败 → exhausted
```

> 不要无限重试：每次调用都花钱，也可能在错误契约上原地打转。

## 4. 消息怎么追加？

失败一轮至少追加两条：

1. `assistant`：这次**原样**输出（让模型看见自己写了什么）
2. `user`：修复指令 = 错误摘要 + 「只输出符合 schema 的 JSON，不要解释」

错误摘要来自 Day 26 的思路：`loc` 路径 + `msg`，人类和模型都读得懂。

## 5. 三类失败，提示可以略有侧重

| 类型 | 典型信号 | 给模型的重点 |
|------|----------|--------------|
| extract | 抽不出 `{...}` / empty | 「请输出一个完整 JSON 对象」 |
| json | `json.loads` 失败 | 「检查逗号/引号/括号」 |
| validation | pydantic 字段错 | 「按下列字段错误逐项改正」 |

今日练习用 `classify_failure` 做轻量分类；repair 正文仍以完整错误列表为主。

## 6. 可测试性：注入 LLM

真实 Agent 难测，是因为网络与非确定性。  
今日把 LLM 做成：

```python
llm: Callable[[list[dict[str, str]]], str]
```

测试里塞一个按队列吐字符串的假模型：先坏后好、始终坏、一次成功——三类路径全覆盖。

## 7. 今日不做的事

- 不接真实 LLM API
- 不改 Day 26 的 Schema 本身（复用 TaskBatch）
- 不做「事实错误」的反思（那是 Reflection / RAG，后面阶段）

## 8. 今日一句话

> Repair loop 的本质：**把类型系统的拒绝理由，翻译成模型下一轮的改稿意见，并给硬顶。**

## 9. 明日预告

Day 28：**从函数到 JSON Schema**——为 Tool Calling 预备「参数契约」。

---

## 我的记录（请自己填写）

1. 我设的 `max_repairs` 在真实项目里会调成多少？依据是什么？  
2. 若模型连续 3 次犯同一字段错误，下一步该人工介入还是改 Schema/Prompt？  
3.  
