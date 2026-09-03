# Day 26 笔记｜JSON 结构化输出

## 1. 今天学什么？

Week 6 开场：把 Day 25 的「手写字段校验」升级成 **Schema 驱动**。

```text
模型回复（可能很脏）
  → 抽出 JSON 对象字符串
    → pydantic model_validate
      → 成功：得到类型安全的 Python 对象
      → 失败：得到「字段路径 + 原因」→ 明日喂回模型修复
```

前端类比：

| 前端 | 今天 |
|------|------|
| TypeScript interface / Zod | pydantic `BaseModel` |
| 表单提交前校验 | 模型输出进程序前校验 |
| OpenAPI 给前后端对齐 | JSON Schema 塞进 Prompt 对齐「模型 ↔ 代码」 |

## 2. 为什么不能只靠 Prompt？

Prompt 可以写「请输出 JSON」，但模型仍会：

- 多写一句「好的，如下：」
- 漏字段、字段名拼错、`priority` 写成 `紧急`
- 数字写成字符串 `"2"`（有时能强转，有时不能）

所以工程上要 **双重契约**：

1. Prompt 里描述期望形状（软约束，提高一次成功率）
2. 代码里用 Schema 硬校验（硬约束，挡住坏数据）

## 3. pydantic v2 最小心智模型

```python
from enum import Enum
from pydantic import BaseModel, Field, ValidationError

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class TaskItem(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    priority: Priority
    tags: list[str] = Field(default_factory=list)
    estimate_hours: float | None = Field(default=None, ge=0)
```

常用入口：

| API | 用途 |
|-----|------|
| `Model.model_validate(dict)` | 已是 dict / 嵌套结构 |
| `Model.model_validate_json(str)` | 一整段 JSON 字符串 |
| `Model.model_json_schema()` | 导出 JSON Schema（可塞 Prompt） |
| `ValidationError.errors()` | 拿结构化错误列表 |

> 记住：`str, Enum` 做枚举时，输入必须是枚举值字符串；非法值直接校验失败——这正是我们想要的。

## 4. 抽取 vs 校验：两步不要搅在一起

| 步骤 | 职责 | 失败意味着 |
|------|------|------------|
| `extract_json_object` | 从脏文本里找到 `{...}` | 模型没吐出对象，或括号烂了 |
| `model_validate` | 字段类型与约束 | 吐出了 JSON，但不合契约 |

分开后，日志和明日的 repair 策略都更清晰：  
「抽不出」和「字段错」要给模型看的反馈不一样。

## 5. Schema 放进 Prompt 的正确姿势

不要把整份巨型 OpenAPI 糊进去。今日练习要求：

- 用 `model_json_schema()` 拿到 schema
- 再压成短文本（缩进 JSON / 去掉 `$defs` 噪音也可以后续优化）
- Prompt 里明确：**只输出符合该 schema 的一个 JSON 对象，不要 Markdown**

前端思维：这等于把「接口文档」塞给对方实现——对方是 LLM。

## 6. 今日不做的事

- 不接真实 LLM（`main.py` 用 mock）
- 不做自动修复重试（那是 Day 27）
- 不引入 langchain / openai SDK

## 7. 今日一句话

> 结构化输出的本质不是「让模型会写 JSON」，而是 **用 Schema 把概率输出关进类型系统**。

## 8. 明日预告

Day 27：**校验失败重试**——把 `ValidationError` 摘要拼回对话，最多修 3 次。

---

## 我的记录（请自己填写）

1. 我最容易写错的字段约束是？  
2. 把 schema 塞进 Prompt 后，mock 之外若接真模型，一次成功率有变化吗？  
3.  
