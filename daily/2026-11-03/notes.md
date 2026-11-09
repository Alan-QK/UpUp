# Day 65 笔记｜周挑战：带记忆助理

## 1. 一句话定位

**带记忆助理**：在对话回路里接入「该不该记 → 怎么存 → 下次怎么取」，并用**磁盘文件**证明记忆能活过进程重启。

## 2. 本周能力拼装图

```text
用户输入
   │
   ├─① search(长期库) ──► 召回块 [长期记忆]
   │                         │
   │                         ▼
   ├─② mock / LLM 回复 ◄── 注入偏好
   │
   └─③ decide_write
         ├ WRITE → upsert → save(JSON)
         ├ ASK   → confirm? → 同上 / 跳过
         └ SKIP  → 不落库
```

| Day | 积木 | 今天怎么用 |
|-----|------|-----------|
| 61 | 短记忆窗口 | 本挑战聚焦长期；短记忆可后续挂在会话层 |
| 62 | 摘要压缩 | 超长会话时再叠；今日不强制 |
| 63 | 向量检索 | `mock_embed` + 余弦 + user 隔离 |
| 64 | 写入闸门 | `decide_write` 三态 |
| **65** | **持久化助理** | `FileMemoryStore` + 两次运行 |

## 3. 前端迁移直觉

| 你熟悉的前端 | 今日对应 |
|--------------|----------|
| `localStorage` / IndexedDB | JSON 记忆文件 |
| 刷新页面状态还在 | 新进程 `load()` 后仍在 |
| 按 userId 分桶缓存 | `user_id` 隔离检索 |
| 表单校验后再 POST | `decide_write` 后再 `upsert` |
| 偏好设置页 | 长期 preference 条目 |

结论：Agent 的「记住我」≈ 带校验的**用户配置持久化**，不是把聊天记录整段 dump。

## 4. 为什么必须「两次运行」验收

只在一个 `MemoryAssistant` 对象里 `append` 再 `search`，只能证明内存结构对——**证明不了跨会话**。

正确姿势：

```text
会话1: MemoryAssistant(path) → 写入 → 进程结束（对象销毁）
会话2: MemoryAssistant(path) → 构造时 load → search → 回复含偏好
```

今日 `run_cross_session_demo` 正是这个剧本。

## 5. 持久化最小约定

```json
{
  "version": 1,
  "items": [
    {
      "id": "mem-xxx",
      "user_id": "u-demo",
      "text": "我喜欢深色主题",
      "kind": "preference",
      "embedding": [0.1, ...],
      "metadata": {"reason": "preference_signal"}
    }
  ]
}
```

生产可换成 SQLite / 向量库；**接口保持 upsert / search / load** 即可换底座。

## 6. 回复策略（今日无 LLM）

教学用 `build_mock_reply`：

- 无召回 → 明确说「还没有长期记忆」
- 有召回 → 「根据我记得的偏好：…」拼进回复，方便单测断言

真实产品里这里换成 Chat API，并把 `context_block` 放进 system / 工具结果。

## 7. 常见坑

1. 把 `_items` 放模块全局 — 测试并行 / 多用户会串味  
2. 构造时不 `load` — 「第二次运行」永远空  
3. 检索不按 `user_id` 过滤 — 隐私事故  
4. 敏感信息走 ASK 而不是 SKIP — 密钥进确认 UI  
5. 用内置 `hash()` 做 embedding — `PYTHONHASHSEED` 一变召回全乱（已用 FNV）

## 8. 和里程碑的关系

Week 13 收束后，Week 14 进入规划（Planner / Plan-and-Execute）。记忆层会成为 `research-crew` 里各角色的共享长期上下文入口——今天先把「单用户助理」跑通。

## 9. 今日口令

> 记得住，是因为写进了文件；取得回，是因为按问题检索——不是因为上下文窗口够大。
