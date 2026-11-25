# Day 19 笔记｜结构化日志与调试

## 1. 今天学什么？

聊天 / Agent 出问题时，最怕的是：

```text
print("calling...")
print(resp)
print("oops", e)
```

这种日志：**人偶尔能看懂，机器几乎用不了**。  
今天练一套最小可用的**结构化日志**：一行一条 JSON，带稳定的 `event` 名和字段。

| 概念 | 前端类比 | 今天对应 |
|------|----------|----------|
| 埋点事件 | `track('checkout_click', {sku})` | `event` + 字段 |
| 控制台等级 | `console.debug/info/warn/error` | `level` |
| 脱敏 | 不把 token 打到 Sentry | `mask_value` / 字段名启发式 |
| 可注入时钟 | 测试里 fake timers | `clock=` 参数 |

## 2. 一条好日志长什么样？

```json
{"ts":"2026-08-14T02:00:00+00:00","level":"info","event":"chat.response","session_id":"s1","model":"fake","latency_ms":12,"completion_chars":18}
```

约定：

1. **`ts`**：ISO8601（UTC 也可；关键是稳定可解析）
2. **`level`**：`debug` / `info` / `warning` / `error`
3. **`event`**：短点分名，如 `chat.request`、`chat.error`
4. **其余字段**：扁平、可 JSON 序列化；不要塞整段超大 prompt（可记长度 / hash）

> 前端同学可以想成：每个事件是一个「埋点」，字段是维度，方便后期过滤「所有 latency_ms > 3000 的 chat.response」。

## 3. 为什么 Agent 特别需要它？

Agent 是多步的：

```text
user → tool.call → tool.result → model.think → tool.call → ... → answer
```

没有事件轨迹时，你只能猜「卡在哪一步」。  
有轨迹时，你可以回答：

- 这次请求用了哪个 model？
- 耗时多久？失败在 request 还是 tool？
- 同一 `session_id` / `trace_id` 下发生了什么？

今天只覆盖聊天一轮的 request / response / error——这是可观测的**最小闭环**。Phase 5 会接到真正的 Tracing。

## 4. 脱敏：日志也是攻击面

常见翻车：

```python
logger.info(f"using key={api_key}")  # 事故现场
```

规则：

- 字段名命中 `api_key` / `authorization` / `*_token` / `*_secret` → 写日志前脱敏
- 短串直接 `***`；长串保留头尾，中间 `***`
- **内容字段**（user 消息）默认可以记长度，今天练习里对消息正文用 preview 截断即可

## 5. 可测试性：注入 sink 与 clock

生产写 stdout / 文件；测试写 `io.StringIO`：

```python
buf = io.StringIO()
logger = StructuredLogger(sink=buf, clock=lambda: fixed_dt)
logger.log("info", "chat.request", model="m")
line = buf.getvalue().strip()
assert json.loads(line)["event"] == "chat.request"
```

不要在单测里 `sleep`，也不要读真实 `/var/log`。

## 6. 和里程碑的关系

明天 Day 20 要打磨 `cli-chatbot`。建议把今天的 logger 接进会话循环：

- `/reset` → `session.reset`
- 每次问答 → `chat.request` / `chat.response`
- 捕获 API 错误 → `chat.error`（再决定是否展示给用户）

## 7. 今日一句话

> 调试 Agent 靠事件轨迹：稳定的 `event` 名 + 可机读字段 + 密钥永不明文。

## 8. 明日预告

Day 20：里程碑 `cli-chatbot`——把 Phase 1 能力收成可演示的命令行聊天机器人。

---

## 我的记录（请自己填写）

1.  
2.  
3.  
