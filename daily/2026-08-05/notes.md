# Day 12 笔记｜角色消息与多轮上下文

## 一句话

**人设靠 `system`，记忆靠把历史 `user`/`assistant` 原样再塞回 `messages`。**

---

## 三个角色，各干一件事

| role | 谁在说话 | 典型用途 |
|------|----------|----------|
| `system` | 产品/开发者写的规则 | 人设、语气、禁止事项、输出格式 |
| `user` | 终端用户 | 本轮提问 |
| `assistant` | 模型曾经说过的话 | 多轮「记忆」——必须回传，模型本身无状态 |

额外角色（本周先不碰）：`tool`（工具结果，Phase 3 再学）。

---

## 无状态 API → 有状态会话

Chat Completions **不帮你存会话**。每次请求都是完整快照：

```text
第 1 轮请求：
  [system, user₁] → assistant₁

第 2 轮请求：
  [system, user₁, assistant₁, user₂] → assistant₂
```

前端类比：

| 前端 | 多轮 Chat |
|------|-----------|
| 服务端 Session / 前端 state | 你本地维护的 `history` 列表 |
| 每次请求带 cookie / token | 每次请求带完整 `messages` |
| Redux store 追加 action | `history.append(user); history.append(assistant)` |

---

## 固定人设怎么写（够用就行）

好的 system 通常包含：

1. **身份**：你是谁  
2. **风格**：简洁 / 中文 / 少废话  
3. **边界**：不会什么、遇到不确定怎么说  

示例（今日练习默认人设的思路）：

```text
你是一名资深前端转 AI Agent 的学习助教。
回答简洁、偏实战，必要时用前端类比解释 Python/LLM 概念。
```

反例：把整本文档塞进 system——又贵又容易被后续 user 冲淡。人设短、规则硬；长资料以后用 RAG（Phase 2）。

---

## `PersonaAssistant` 的最小职责

今天练习把「会话状态」从裸 `complete(messages)` 里抽出来：

```text
ask(user_text):
  messages = [system] + history + [user]
  reply = client.complete(messages)
  history += [user, assistant(reply)]
  return reply

reset():
  history.clear()   # 人设保留
```

注意：

- `history()` 应返回**副本**，避免调用方 `clear()` 误伤内部状态  
- 空 `system` / 空 `user` 直接 `ValueError`，别默默发垃圾请求  
- `system` 建议 `strip()` 后保存，构造时允许首尾空白

---

## 常见坑

1. **忘了回传 assistant**：第二轮模型「失忆」  
2. **每轮改写 system**：人设漂移，调试困难；今天固定一份  
3. **history 含 system**：容易重复两条 system；约定 history 只存 user/assistant  
4. **无限追加**：上下文会爆（token）；裁剪是 Day 16，今天先感知「会变长」

---

## 和本周路线的关系

```text
Day 11  非流式第一次调用
Day 12  system + 多轮上下文     ← 今天
Day 13  流式输出（边生成边打字）
Day 14  token / 成本日志
Day 15  周挑战：内存多轮 CLI（/reset /exit）
```

---

## 延伸（可选）

- 试着对比：`--demo` 多轮 vs `--demo --reset-between`（每轮清空）  
- 想一想：若要把会话存盘，序列化 `history()` 的 JSON 就够起步了（Day 15/16）
