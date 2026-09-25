# Day 11 笔记｜Chat Completions 第一次调用

## 一句话

把 LLM 当成一个 **JSON HTTP API**：你发 messages，它回一段 assistant 文本。

---

## 为什么从协议学起（而不是先装 SDK）

前端同学已经很熟 REST。Chat Completions 本质上就是：

```http
POST /v1/chat/completions
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

官方 SDK（`openai` Python 包）只是帮你拼请求、解析响应。先手写一遍，后面换厂商、写 Agent 循环、做 Mock 都会轻松很多。

---

## 请求体最小形状

```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "user", "content": "用一句话解释什么是 Agent"}
  ],
  "stream": false
}
```

| 字段 | 含义 |
|------|------|
| `model` | 模型名（各厂商字符串不同） |
| `messages` | 对话列表；今天先只发一条 `user` |
| `stream` | `false` = 等整段回复再返回（非流式） |

可选：`temperature`（随机性）、`max_tokens`（上限）——本周后面再细抠。

### 角色（先记三个）

| role | 谁在说话 | 今天 |
|------|----------|------|
| `system` | 系统人设/规则 | Day 12 重点 |
| `user` | 用户 | ✅ 今天用 |
| `assistant` | 模型历史回复 | Day 12 多轮 |

---

## 响应体你要读哪些字段

成功时大致长这样（字段名以 OpenAI 兼容为准）：

```json
{
  "id": "chatcmpl-...",
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "finish_reason": "stop",
      "message": {
        "role": "assistant",
        "content": "Agent 是能感知目标并调用工具行动的程序。"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 18,
    "total_tokens": 38
  }
}
```

取值路径（记牢）：

- 文本：`choices[0].message.content`
- 结束原因：`choices[0].finish_reason`（常见 `stop` / `length`）
- 用量：`usage.*`（计费与限流都看它；Day 14 再算钱）

---

## base_url 怎么拼

`.env.example` 里约定：

```text
OPENAI_BASE_URL=https://api.openai.com/v1
```

客户端应对 `base_url` 发 path：`/chat/completions`  
→ 最终 URL：`https://api.openai.com/v1/chat/completions`

许多国产/网关也是「OpenAI 兼容」：换 `BASE_URL` + `MODEL` + `API_KEY` 即可，协议不变。

---

## 错误怎么分

和 Day 6/7 同一套工程直觉：

| 情况 | 建议 |
|------|------|
| HTTP 401/403 | Key 错或没权限 → 别重试，修配置 |
| HTTP 429 | 限流 → 可退避重试（Day 7） |
| HTTP 5xx / 超时 | 瞬时故障 → 可重试 |
| 200 但缺 `choices` | 协议/网关异常 → 当响应错误抛出 |

今天练习只要求：**非 2xx**、**非法 JSON**、**缺 choices/content** 三类抛清晰异常；重试留给以后叠。

---

## 前端类比（帮你建立心智模型）

| 前端 | LLM API |
|------|---------|
| `fetch('/api')` + JSON | `POST /chat/completions` |
| 请求体 props | `messages` + `model` |
| 响应 `data.result` | `choices[0].message.content` |
| Loading 等到整包 | 非流式（今天）；流式 ≈ SSE（Day 13） |
| Auth Header | `Bearer` API Key |

---

## 安全提醒（重复三遍也不厌）

1. Key 只从环境变量读，不写进源码  
2. 日志里脱敏（Day 9 的 `mask_secret`）  
3. 单测与 Demo 用 Mock，避免误烧额度  

---

## 和本周路线的关系

```text
Day 11  非流式第一次调用     ← 今天
Day 12  system + 多轮上下文
Day 13  流式输出（边生成边打字）
Day 14  token / 成本日志
Day 15  周挑战：内存多轮 CLI
```

---

## 延伸（可选）

- OpenAI API Reference：Chat Completions  
- 你常用的兼容网关文档：对照 `base_url` 与模型名即可
