# Day 30 笔记｜周挑战：会议纪要结构化

## 1. 今天学什么？

Week 6 每天练一块积木：

| Day | 积木 |
|-----|------|
| 26 | JSON + pydantic |
| 27 | 校验失败 → repair |
| 28 | 函数签名 → tool schema |
| 29 | 批量抽取 + CSV 导出 |
| **30** | **嵌套结构化交付（周挑战）** |

今天不学新库，把积木拼成一条真实业务流水线：

```text
会议原文（杂乱）
  → Prompt（角色/任务/约束/Schema）
  → LLM（mock 或真实）
  → 抽 JSON → MeetingMinutes（含 ActionItem[]）
  → Markdown（给人） / CSV（给跟进表）
```

## 2. 决议 vs Action Item

很多人第一次设计字段会全塞进 `todos`。更好的拆法：

| 类型 | 含义 | 例子 |
|------|------|------|
| **决议 decision** | 会上已拍板的结论（事实） | 「Q4 采用方案 B」 |
| **行动项 action item** | 会后要做的事（任务） | 「小王在 9/10 前提交报价」 |

Action item 最少要有：

1. **owner**：谁负责（没有负责人 ≈ 不会发生）
2. **task**：做什么
3. **due_date**（可选但强烈建议）：何时完成
4. **priority**（可选）：`high | medium | low`

前端类比：决议像「公告」；行动项像看板卡片（assignee + title + due）。

## 3. 嵌套 Schema 为什么重要？

Day 29 的 `Contact` 是扁平的。会议纪要天然嵌套：

```json
{
  "title": "Sprint 评审",
  "meeting_date": "2026-09-02",
  "attendees": ["Alice", "Bob"],
  "decisions": ["延期上线一周"],
  "action_items": [
    {"owner": "Alice", "task": "更新发布计划", "due_date": "2026-09-05", "priority": "high"}
  ]
}
```

Agent 落地时，嵌套结构几乎是默认形态：订单含明细、工单含评论、RAG 答案含 citations。今天练的是「一次校验整棵树」。

约束建议（写进 Prompt）：

- 只依据【会议原文】，禁止臆造未出现的人名/日期/决议
- 原文没有截止日期 → `due_date: null`，不要瞎编
- 至少产出 1 条决议 **或** 1 条行动项（空会议无意义）
- 只输出一个 JSON 对象

## 4. 日期规范化

模型常吐出：`2026年9月2日`、`2026/09/02`、`2026-09-02`。  
入库前统一成 **`YYYY-MM-DD`**，下游 CSV / 日历 / 排序才稳。

练习里的 `normalize_date`：

- 空 → `None`
- 已是 `YYYY-MM-DD` → 原样
- `YYYY/M/D`、`YYYY年M月D日` → 转标准格式
- 认不出但非空 → `ValueError("invalid date")`

在 `parse_minutes` 里对 `meeting_date` 与每条 `due_date` 先 normalize，再 `model_validate`。

## 5. 双交付物

| 输出 | 给谁 | 用途 |
|------|------|------|
| Markdown | 人 | 会后同步、评审、贴群 |
| Action Items CSV | 表格 / 项目管理 | 导入 Notion / 飞书多维表 / Jira |

和 Day 29 一样：JSON 给程序，CSV 给人用的表。周挑战多一条 Markdown，因为纪要本身就是「给人读的产品」。

## 6. complete_fn 注入（可测性）

```python
CompleteFn = Callable[[list[dict[str, str]]], str]
```

测试与 `main.py` 注入 mock；接真模型时只换这一处。  
前端思维：把 `fetch` 抽成依赖注入，不测网络测编排。

## 7. 和下周的关系

Week 7 开始 **RAG**：先把文档加载干净、切成 chunk，再谈检索。  
今天练的「非结构化文本 → 结构化对象」在 RAG 管线里依然有用（例如从 chunk 抽标题/实体做元数据）。

## 8. 纸上 2 分钟

原文只写了「决定采用方案 A」，没有任何待办。问：

- `decisions` 应有几条？
- `action_items` 可以为空吗？（按今日 Schema：可以，只要决议非空）
- CSV 数据行应有几行？

答案：决议 1 条；行动项可空；CSV 仅表头（0 行数据）。
