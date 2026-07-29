# Day 7 笔记｜超时、重试与错误分类

## 1. 为什么今天单独讲「失败」？

调 LLM / 工具 API 时，失败是常态：

- 网关偶发 502
- 限流 429
- DNS / TLS 抖动
- 模型侧排队导致超时

Agent Loop 里如果「一次失败就整条任务崩」，产品体验会很差。  
今天目标不是「永不失败」，而是：**可恢复的失败自动缓一下再试；不可恢复的立刻告诉上层。**

| 前端直觉 | Python / Agent |
|----------|----------------|
| axios retry 插件 | 自写 retry wrapper |
| `AbortSignal` 超时 | `httpx.TimeoutException` |
| 401 → 跳登录（别傻重试） | 4xx 多数不重试 |
| 502 → 再试一次 | 5xx / 超时可重试 |

## 2. 先分类，再重试

```text
请求失败
  ├─ 超时 / 连接失败     → 可重试（瞬时）
  ├─ 429 Too Many Requests → 可重试（限流，配合退避）
  ├─ 5xx                   → 可重试（服务端抖）
  ├─ 4xx（除 429）         → 不重试（改请求才有用）
  └─ 业务 JSON 解析失败    → 不重试（响应形态坏了）
```

一句话规则：

> **重试解决的是「偶然」，不是「写错」。**

## 3. 超时是第一道闸门

Day 6 已强调：每个请求必须有 timeout。今天再补一层语义：

```python
import httpx

try:
    httpx.get(url, timeout=5.0)
except httpx.TimeoutException:
    # 可重试候选
    ...
except httpx.TransportError:
    # 连接失败等，也可重试候选
    ...
```

Agent 场景建议：

- 普通工具调用：3–15 秒
- LLM 非流式：30–120 秒（看模型与 max_tokens）
- 流式：读超时要单独考虑（Day 13 再展开）

**无超时 = 线程/协程可能永久挂起**，比抛错更难排查。

## 4. 重试参数：少而可控

今日练习用的最小配置：

| 参数 | 含义 | 建议默认 |
|------|------|----------|
| `timeout` | 单次请求超时（秒） | 5–10 |
| `max_retries` | **额外**重试次数 | 2（总共最多 3 次） |
| `backoff_seconds` | 退避基数 | 0.05–0.5（测试里用很小） |

退避（今天用线性，够学概念）：

```text
第 0 次失败后 sleep = backoff * 1
第 1 次失败后 sleep = backoff * 2
...
```

生产里常见指数退避 + 抖动（jitter），避免雪崩；你以后加一行 `2 ** attempt` 即可，今天先别复杂化。

## 5. 包装器结构（叠在 Day 6 之上）

```text
RetryingJsonClient
  ├─ 内部持有 httpx.Client（同 Day 6）
  ├─ get_json / post_json
  └─ _request_with_retry(...)
        ├─ 分类异常 / 状态码
        ├─ 可重试 → sleep → 再试
        └─ 不可重试或次数用尽 → 抛出
```

对应前端：你们封装的 `request` 层里统一 interceptor，而不是每个页面自己 `for` 循环。

## 6. 和 Agent 的关系（先建立直觉）

以后 Agent Loop 里至少两层重试，别混为一谈：

1. **传输层重试**（今天）：HTTP 超时 / 502 —— 对同一请求再发
2. **任务层重试 / 修复**：工具参数非法、模型输出不合格 —— 换策略再问模型（Phase 3）

今天只做第 1 层。做厚一点，后面接 LLM 会省很多「偶发红字」。

## 7. 测试怎么证明「重试发生了」？

用 MockTransport 记调用次数：

```python
calls = {"n": 0}

def handler(request):
    calls["n"] += 1
    if calls["n"] < 3:
        return httpx.Response(503, json={"error": "busy"})
    return httpx.Response(200, json={"ok": True})
```

断言：`calls["n"] == 3` 且最终拿到 `{"ok": True}`。  
这比真打外网稳 100 倍。

## 8. 今日一句话

> 稳健网络层 = 必超时 + 错误分类 + 有上限的退避重试。

## 9. 明日预告

Day 8：`asyncio` 基础——并发请求 3 个 URL 并汇总，建立 Agent 并行工具调用的直觉。

---

## 我的记录（请自己填写）

1.  
2.  
3.  
