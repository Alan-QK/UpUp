# Day 13 笔记｜流式输出（SSE / chunk 打印）

## 一句话

**流式就是：同一次补全，把「整包 JSON」拆成一串带 `data:` 前缀的增量包；你边收边显示。**

---

## 非流式 vs 流式（前端直觉）

| | 非流式（Day 11） | 流式（今天） |
|--|------------------|--------------|
| 请求字段 | `"stream": false` | `"stream": true` |
| 响应形态 | 一个 JSON object | `text/event-stream`（SSE） |
| 文本位置 | `choices[0].message.content` | 多个 `choices[0].delta.content` |
| 读取方式 | `resp.json()` | `for line in resp.iter_lines()` |
| 前端类比 | 等接口整包返回再渲染 | `ReadableStream` / EventSource 边到边画 |

Agent 产品几乎都要流式：用户感知延迟从「整句出来」降到「第一个字出来」。

---

## SSE 长什么样

典型片段（简化）：

```text
data: {"id":"chatcmpl-1","choices":[{"delta":{"role":"assistant"},"index":0}]}

data: {"id":"chatcmpl-1","choices":[{"delta":{"content":"你"},"index":0}]}

data: {"id":"chatcmpl-1","choices":[{"delta":{"content":"好"},"index":0}]}

data: {"id":"chatcmpl-1","choices":[{"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

约定（今日练习采用的最小子集）：

1. 只关心以 `data:` 开头的行（忽略空行、`:` 注释行）
2. `data:` 后面可以有一个可选空格：`data: {...}` 或 `data:{...}`
3. payload 为 `[DONE]` → **结束迭代**（不要当 JSON 解析）
4. 其余 payload → `json.loads`，再取增量文本
5. 没有 `content`、或 `content` 不是 `str` → 跳过（首包常只有 `role`）

---

## httpx 怎么读流

```python
with client.stream("POST", "/chat/completions", json=payload) as resp:
    if resp.status_code < 200 or resp.status_code > 299:
        # 错误体也要读完，避免连接悬挂
        body = resp.read().decode("utf-8", errors="replace")
        raise ChatHttpError(resp.status_code, body)
    for line in resp.iter_lines():
        ...
```

注意：

- 必须用 **`stream()` 上下文**，不要 `post()` 后再幻想「边下边读」
- 状态码非 2xx 时先 `read()` 再抛错（与 Day 11 的 `ChatHttpError` 一致）
- Mock 测试里把整段 SSE 字节塞进 `httpx.Response(content=...)` 即可离线验证

---

## 终端「打字机」效果

核心就两行：

```python
print(chunk, end="", flush=True)
# 全部结束后补一个换行
print(file=file)
```

`flush=True` 很关键：否则 stdout 缓冲会让你感觉「还是整段蹦出来」。  
拼完整回复：边 print 边 `parts.append(chunk)`，最后 `"".join(parts)`。

---

## 和多轮 / Agent 的关系

- **流式只改变传输形态**，不改变「无状态 + 本地拼 messages」（Day 12）
- 流结束后，你仍要把完整 assistant 文本写进 history
- 工具调用场景里，流式 chunk 还可能带 `tool_calls` 增量（Phase 3）；今天只处理纯文本 `delta.content`

```text
Day 11  非流式 complete
Day 12  system + 多轮历史
Day 13  流式 SSE 打印          ← 今天
Day 14  token / 成本
Day 15  周挑战：内存多轮 CLI
```

---

## 常见坑

1. **仍去读 `message.content`**：流式中间包没有它，应读 `delta.content`
2. **忘记 `stream: true`**：服务端仍返回整包 JSON，你的 SSE 解析会全挂
3. **把 `[DONE]` 当 JSON**：直接 `json.loads` 会炸
4. **不 flush**：本地 Demo 也可能看起来「不流」
5. **错误响应当流解析**：先检查 status，再 `iter_lines`

---

## 延伸（可选）

- 把 Day 12 的 `PersonaAssistant.ask` 改成内部调 `iter_content` + `print_stream`
- 想一想：前端收到 SSE 时，如何把「未完成的半句」渲染成气泡（不必今天写）
