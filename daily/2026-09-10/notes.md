# Day 36 笔记｜最小 RAG 生成链路

## 1. 今天在路线图里的位置

```text
Week 7：能「找得到」（检索 CLI）
        ↓
Week 8 Day 36：把 hits 塞进 Prompt，让模型「基于资料答」
        ↓
D37 引用溯源 · D38 拒答 · D39 评测 · D40 mini-rag 里程碑
```

真正的 RAG = **Retrieve + Augment + Generate**，缺一不可。

## 2. 三步分别干什么？

| 步骤 | 输入 | 输出 | 今日函数 |
|------|------|------|----------|
| Retrieve | 问题 + 向量库 | top-k 片段 | `retrieve` |
| Augment | 问题 + 片段 | Chat messages | `format_context_block` + `build_rag_messages` |
| Generate | messages | 答案文本 | `generate_fn`（可注入） |

`run_rag` 只是把三步串起来——编排层，不藏魔法。

## 3. 前端类比

| 前端 | RAG |
|------|-----|
| 搜索 API 返回 hits | Retrieve |
| 把 hits 渲染进「发给后端的上下文」或 Prompt 模板 | Augment |
| 调用模型 / 展示流式回答 | Generate |
| props 注入 mock | `GenerateFn` 注入假函数 |

你熟悉「数据 → 视图模型 → 渲染」。RAG 是「检索结果 → Prompt 视图 → 模型渲染」。

## 4. Prompt 为什么要结构化？

练习里的 user 消息固定三段：

```text
参考资料：
[1] source=... score=... id=...
<chunk text>

问题：...

请基于参考资料回答。
```

好处：

- 模型知道边界（资料 vs 问题）
- 后面做引用时，编号 / source 已经在上下文里
- 单测可以精确断言字符串，避免「玄学 Prompt」

System 消息负责**行为约束**：「只根据参考资料；不足就说不知道」。

## 5. 为什么 Generate 要可注入？

生产环境你会接 OpenAI 兼容 API；练习环境要：

- 无 Key、无外网、可重复  
- 断言「拼进 Prompt 的内容」而不是「模型心情」

所以 `run_rag(..., generate_fn=...)`。把 Day 11 的 `ChatClient.complete` 包一层就能替换假函数。

## 6. 常见误解

| 误解 | 纠正 |
|------|------|
| 检索分数高 = 答案对 | 分数只是相似度；答案质量看生成与引用 |
| 把整库塞进 Prompt | 贵、慢、注意力稀释；只要 top-k |
| 没有资料也硬答 | 应拒答（D38）；今天至少在 system 里声明 |

## 7. 今日一句话

> RAG = 先找片段，再把片段写进 Prompt，最后才让模型说话。

## 8. 明日预告

Day 37：引用溯源 —— 答案附带来源 chunk，让前端能点开 `source#index`。

---

## 我的记录（请自己填写）

1.  
2.  
3.  
