# Phase 2｜Prompt、结构化输出与 RAG 入门

> 周期：Week 5–8（约 20 个工作日）  
> 关键词：Prompt 模式、JSON Schema、Embedding、切分、检索、引用

---

## 阶段目标

1. 能系统化设计 Prompt，而不是「玄学试错」
2. 强制模型输出可校验的结构化数据，失败可重试
3. 搭一条最小 RAG：文档 → 切分 → 向量化 → 检索 → 生成
4. 交付里程碑：`projects/mini-rag`

---

## 周计划

### Week 5 · Prompt Engineering 系统化

| Day | 主题 | Coding |
|-----|------|--------|
| D21 | Prompt 组成：角色、任务、约束、格式 | Prompt 模板库 |
| D22 | Few-shot 与反例 | 分类/抽取任务 |
| D23 | 思维链 vs 直接答案 | 对比实验 |
| D24 | 防注入与边界声明（入门） | 恶意输入测试 |
| D25 | 周挑战：需求文档 → 用户故事生成器 | 模板化生成 |

### Week 6 · 结构化输出

| Day | 主题 | Coding |
|-----|------|--------|
| D26 | JSON 输出与 schema 校验 | pydantic 模型 |
| D27 | 校验失败重试策略 | Repair loop |
| D28 | 工具参数 schema 设计预热 | 函数签名 → schema |
| D29 | 批量抽取（发票/简历字段等） | 批处理脚本 |
| D30 | 周挑战：会议纪要结构化 | 输出 action items |

### Week 7 · RAG 基础链路

| Day | 主题 | Coding |
|-----|------|--------|
| D31 | 文档加载与清洗 | txt/md loader |
| D32 | Chunking 策略 | 固定/重叠切分 |
| D33 | Embedding API | 向量化脚本 |
| D34 | 向量库入门（Chroma） | 写入与查询 |
| D35 | 周挑战：本地笔记库检索 | top-k 检索 CLI |

### Week 8 · RAG 生成与质量

| Day | 主题 | Coding |
|-----|------|--------|
| D36 | Retrieve → Augment → Generate | 最小问答 |
| D37 | 引用溯源（展示 chunk 来源） | citations |
| D38 | 检索失败与拒答策略 | 「不知道」 |
| D39 | 简单评测：命中率/人工抽检 | eval 表格 |
| D40 | 里程碑：`mini-rag` 验收 | 项目打磨 |

---

## 里程碑验收清单

- [ ] 支持至少一种文档格式（md/txt/pdf 任选）
- [ ] 可配置 chunk size / overlap
- [ ] 问答返回答案 + 引用来源
- [ ] 无相关上下文时能拒答或低置信提示
- [ ] README 含架构示意（可用 mermaid）
- [ ] 准备 5 条问答样例作为 golden set 雏形

---

## 易踩坑

- chunk 过大 → 检索噪声；过小 → 上下文破碎
- 只追求「能答」不看引用是否正确
- Prompt 过长导致成本与注意力稀释

## 完成后进入

→ [Phase 3：Agent 核心](./phase-03-agent-core.md)
