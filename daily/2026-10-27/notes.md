# Day 61 笔记｜会话记忆回顾（增强历史窗口）

## 1. 一句话定位

**短时会话记忆（short-term / working memory）** = 当前这次对话里，模型「当场能看见」的消息集合。

Phase 1 Day 16 你做过最朴素的办法：按轮数滑动窗口。  
今天进入 Phase 4，把它升级成**可观测的增强策略**：轮数上限 + token 预算 + 钉住（pinned）关键事实。

## 2. 前端迁移直觉

| 你熟悉的前端 | Agent 短记忆 |
|--------------|--------------|
| 聊天 UI 虚拟列表只渲染附近消息 | 请求只带窗口内 messages |
| Local state / Zustand store 有上限 | 内存里的 history list 也要裁 |
| 置顶公告 / sticky header | `pinned=True` 的消息不被裁掉 |
| Performance budget（包体积 / 请求体） | `max_tokens` 预算 |
| DevTools 里看「丢掉了哪些 props」 | `WindowResult.dropped` + stats |

结论：短记忆不是「越大越好」，而是**在预算内保留对当前任务最有用的上下文**。

## 3. 三种记忆先分清（本周地图）

```text
短记忆（今天）     摘要记忆（D62）     长期向量记忆（D63）
├─ 当前会话窗口     ├─ 旧轮压成摘要     ├─ 跨会话偏好/事实
├─ 随请求发送       ├─ 仍挂在会话里     ├─ 按需召回
└─ 实现：裁剪策略   └─ 实现：summarize  └─ 实现：embed + search
```

今天只做**短记忆增强**。不要一上来上向量库——那是用大炮打蚊子。

## 4. Day 16 → Day 61：增强点

| Day 16 | Day 61 |
|--------|--------|
| 只按 `max_turns` 裁 | `max_turns` **和/或** `max_tokens` |
| system 单独字段 | system 可在列表里，但**默认永不裁** |
| 无「重要消息」概念 | `pinned`：关键事实抗裁剪 |
| 返回裁后 list | 返回 `WindowResult`（kept + dropped + stats） |
| 难回答「为什么忘了」 | 报告能说清丢掉了什么 |

组合规则（练习约定）：

1. **先保护**：`role=system`（若 `keep_system`）与 `pinned=True` 进入保留池  
2. **再按轮**：对其余消息按完整 `user+assistant` 轮从新到旧取，受 `max_turns` 限制  
3. **再按预算**：若设了 `max_tokens`，从**最新**往旧加，估 token 超标则停（pinned/system 已占用预算）  
4. **最后排序**：输出仍按原相对顺序

## 5. Token 估算（教学用）

真实项目会接 tiktoken / 厂商 tokenizer。今天用标准库启发式即可：

```text
estimate_tokens(text) ≈ max(1, (len(text) + 3) // 4)   # 空串为 0
```

够用来练「预算裁剪」的分支，不必纠结中英 token 差。

## 6. 常见坑

| 坑 | 正确做法 |
|----|----------|
| 裁成半轮（只剩 assistant） | 按完整轮取；不成对条目跟轮策略一起处理或丢弃 |
| pinned 把预算撑爆 | stats 里如实报告；策略仍保留 pinned（产品上再决定是否拒绝） |
| 原地改入参 list | 始终返回新 list / 新 Result |
| 只裁发送、本地无限涨 | 会话对象追加后也应再 `apply` 一次（与 Day 16 一致） |

## 7. 和 Agent Loop 的关系

Tool-agent（Day 60）每步都可能往 messages 塞 tool 结果。短记忆策略通常挂在：

```text
用户输入
  → 追加到 session.history
  → apply_enhanced_window(...)   ← 今天
  → 送给 LLM / Agent Loop
  → 追加 assistant / tool 消息
  → 再次 window（可选）
```

没有这一层，Loop 跑几步就会又贵又撞上下文上限。

## 8. 明日预告

Day 62：**摘要记忆**——窗口外的旧轮不再直接丢掉，而是压成一段 summary 继续挂在上下文里。
