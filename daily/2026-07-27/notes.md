# Day 6 笔记｜HTTP 与 httpx

## 1. 为什么 Week 2 从 HTTP 开始？

调 LLM = 发一个 **HTTPS POST JSON**，再读回 JSON。  
Agent 的工具调用、RAG 检索、回调 Webhook，本质也都是 HTTP。

| 前端直觉 | Python（今天） |
|----------|----------------|
| `fetch(url)` / `axios.get` | `httpx.get(url)` |
| `res.json()` | `response.json()` |
| `AbortSignal` / timeout | `timeout=10.0` |
| `baseURL`（axios） | `httpx.Client(base_url=...)` |

先把「同步 HTTP 客户端」写稳，明天再加重试，后天再上 `asyncio`。

## 2. 最小可用示例

```python
import httpx

# 一次性请求（简单脚本够用）
r = httpx.get("https://httpbin.org/get", params={"q": "agent"}, timeout=10.0)
r.raise_for_status()
data = r.json()

# 可复用 Client（推荐：连接池 + 默认 base_url / timeout）
with httpx.Client(base_url="https://api.example.com", timeout=10.0) as client:
    r = client.post("/v1/chat", json={"message": "hi"})
    print(r.status_code, r.json())
```

要点：

1. **timeout 必写**（秒，可以是 float）
2. **JSON 请求体**用 `json={...}`，不要自己 `json.dumps` 再塞 `content=`（除非你很清楚 Content-Type）
3. **读 JSON**用 `.json()`；非 JSON 会抛异常——今天练习里我们把它包装成业务异常

## 3. 封装一层：JsonClient

业务代码直接写 `httpx` 会很快散落：

- 每处重复 timeout / header
- 状态码处理不一致
- 以后换 base_url（代理、国内兼容网关）要改十几处

最小封装：

```text
JsonClient
  ├─ base_url / timeout / headers
  ├─ get_json(path, params=...)
  └─ post_json(path, json=...)
```

对应前端：你们公司里的 `request.get/post` 封装，或 axios instance。

**错误分层（今天够用的两档）**：

| 异常 | 何时抛 | 前端类比 |
|------|--------|----------|
| `HttpStatusError` | HTTP 状态码不在 200–299 | `!res.ok` |
| `HttpResponseError` | 状态 OK 但 body 不是合法 JSON | `res.json()` 解析失败 |

明天 Day 7 会再拆：超时 / 连接失败 / 可重试 5xx 等。

## 4. 测试：MockTransport（不连外网）

Agent 练习环境经常没外网，或外网不稳定。`httpx.MockTransport` 让你在进程内伪造响应：

```python
def handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/ping":
        return httpx.Response(200, json={"ok": True})
    return httpx.Response(404, json={"error": "missing"})

transport = httpx.MockTransport(handler)
client = httpx.Client(base_url="https://mock.local", transport=transport)
```

今日练习的 `JsonClient` 接受可选的 `transport=`，测试时注入 Mock，生产代码不传即可。

## 5. 和 LLM API 的关系（先瞄一眼）

以后你会写类似：

```python
client.post_json(
    "/v1/chat/completions",
    json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "你好"}],
    },
)
```

今天把「POST JSON → 拿回 dict」这条管道打通即可，不必纠结模型字段。

## 6. 今日一句话

> HTTP 客户端是 Agent 的网线；先封装稳、测得过，再谈模型与编排。

## 7. 明日预告

Day 7：超时、重试与错误分类——把「偶发 502 / 超时」变成可恢复行为。

---

## 我的记录（请自己填写）

1.  
2.  
3.  
