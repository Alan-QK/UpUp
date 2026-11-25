# Day 51 笔记｜框架选型原则（少而精）

## 1. 今天学什么？

你已经手写过 Agent Loop、终止条件、错误恢复、Trace、只读工具沙箱。  
从今天起进入 Week 11：**对照一个框架**，而不是「把框架当黑盒调通」。

| 问题 | 坏答案 | 好答案 |
|------|--------|--------|
| 该学哪个框架？ | 全都学一遍 | 先定目标，再选 **1** 个深入 |
| 什么时候上框架？ | 第一天就上 | **先手写最小 Loop**，再映射到框架抽象 |
| 框架能替代什么？ | 替代理解 | 只替代样板代码与编排便利 |

前端类比：

- 手写 Loop ≈ 自己写过一次 mini Redux / 状态机
- 上框架 ≈ 再去用 Zustand / XState——因为你懂状态流转，库才是加速器

## 2. 候选清单（本课程刻意收窄）

| 候选 ID | 一句话定位 | 更适合 |
|---------|------------|--------|
| `handwritten` | 自己管 messages / tools / stop | **学习**、强可控、面试讲得清 |
| `langchain` | 通用链式/工具编排生态 | 快速拼装、资料多（抽象也厚） |
| `langgraph` | 图 / 状态机式 Agent | 多步状态、多智能体、可恢复流程 |
| `openai_agents_sdk` | 官方 Agent 抽象 | 紧贴 OpenAI 协议、想少一层胶水 |
| `llamaindex` | 偏 RAG / 数据连接 | 文档问答、索引与检索优先 |

> 名字会变、版本会碎。记住的是**选型维度**，不是背品牌。

## 3. 四个硬维度（练习会编码）

1. **目标（goal）**  
   `learn_loop` / `ship_product` / `rag_app` / `multi_agent`
2. **团队 Python 熟练度**  
   偏弱时更应先 `handwritten`，避免同时学语言 + 厚框架
3. **能力需求**  
   要不要多智能体？要不要 RAG 优先？要不要官方 SDK？
4. **数量上限 `max_frameworks`**  
   本阶段建议 **1**；最多 **2**（主选 + 备胎），禁止「食堂打饭式」全选

## 4. 今日推荐规则（刻意简化，方便落地）

```text
if goal == learn_loop OR python_level == beginner:
    primary = handwritten
elif goal == multi_agent:
    primary = langgraph
elif goal == rag_app:
    primary = llamaindex
elif prefer_official_sdk:
    primary = openai_agents_sdk
else:  # ship_product 等
    primary = langchain

备胎：在剩余候选里按「互补」挑 1 个（受 max_frameworks 限制）
```

互补直觉：

- 主选 handwritten → 备胎常选一个「对照框架」（如 langgraph / openai_agents_sdk）
- 主选 RAG 框架 → 备胎可以是 handwritten（保住对 Loop 的掌控）
- 主选已是框架且 max_frameworks=1 → 无备胎

## 5. 一页选型笔记应有什么？

练习要求 `render_selection_note` 至少包含：

1. 项目目标与约束  
2. 主选 +（可选）备胎  
3. **为什么选它**（对照维度，别写广告词）  
4. **为什么不选其他**（各一句弃选理由）  
5. **下一步行动**（例如：用框架重写 Day50 只读文件助手）

篇幅控制在「一页」：能让同事 3 分钟读完并拍板。

## 6. 常见坑

| 坑 | 症状 | 纠正 |
|----|------|------|
| 框架收藏家 | 周更三个教程仓库 | 锁 1 个主选，跑通同能力对照 |
| 跳过手写 | 会 import，不会排错 Loop | 先完成 Week 10，再映射概念 |
| 用框架学 RAG+Agent+MultiAgent 一次 | 概念糊成浆 | 一次只加一个能力轴 |
| 版本焦虑 | 文档对不上 API | 锁定小范围官方示例，先跑通 happy path |

## 7. 今日一句话

> 框架是放大器：你懂 Loop，它放大产能；你不懂 Loop，它放大困惑。

## 8. 明日预告

Day 52：框架重写手写 Agent——把 Week 10 的能力映射到框架概念（可用薄封装 / mock，重在对照）。

---

## 我的记录（请自己填写）

1. 我当前练习项目的 goal：  
2. 我的主选 / 备胎：  
3. 我明确弃选的框架及理由：  
