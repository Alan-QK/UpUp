# Day 29 笔记｜批量信息抽取

## 1. 今天学什么？

Day 26–27：把**一条**模型输出变成可校验对象（必要时 repair）。  
Day 28：告诉模型「工具长什么样」。  
今天：**多条文本 → 多条结构化记录 → 导出文件**。

```text
[文本1, 文本2, …文本N]
    → 对每条：Prompt + LLM + 抽 JSON + pydantic
        → ExtractResult(source_id, ok, contact?, error?)
            → 成功子集 → JSON / CSV
            → 失败子集 → 日志 / 重跑队列
```

这是 Agent 落地里极常见的「ETL 味」任务：简历字段、发票抬头、客服工单标签、名片 OCR 后结构化……

## 2. 为什么要「批」而不是只 demo 一条？

| 单条 Demo | 批量流水线 |
|-----------|------------|
| 开心路径 | 部分失败是常态 |
| 打印一下 | 要有对账 id |
| 人眼看结果 | 要导出给表格 / 下游 API |

前端类比：

| 前端 | 今天 |
|------|------|
| 表单 `v-model` 绑一个联系人 | `Contact` pydantic 模型 |
| 批量导入 Excel，一行失败标红 | `ExtractResult.ok=False` + `error` |
| 下载 CSV | `contacts_to_csv` |
| `requestId` 方便排查 | `source_id` |

## 3. 隔离失败（最重要工程习惯）

```python
for source_id, text in items:
    try:
        contact = parse_one(llm(text))
        results.append(ok(...))
    except Exception as e:
        results.append(fail(source_id, e))  # 不要 raise 中断整批
```

原则：

1. **一条坏数据不杀死整批**（除非你显式要求 fail-fast）
2. 错误信息要能定位：`source_id` + 简短 reason
3. 汇总：`total / ok / failed` —— 给人和给监控都好用

Day 27 的 repair loop 仍然有用：你可以在 `extract_one` 内部对**单条**做 1–2 次修复；批量层只负责编排与汇总。今日练习为控复杂度，**批层不做自动 repair**（留给你课后加分）。

## 4. Prompt 怎么写才利于抽取？

固定四段（与 Week 5/6 一致）：

1. **角色**：信息抽取员，只依据原文
2. **任务**：抽出指定字段；原文没有的字段填 `null`，禁止臆造
3. **约束**：只输出一个 JSON 对象；邮箱/电话格式约定
4. **输出格式**：贴上 JSON Schema（`model_json_schema()`）

用户消息里建议明确包裹原文：

```text
【原文】
...粘贴的名片/备注...
【原文结束】
```

防止模型把「说明文字」当成待抽取内容（和 Day 24 注入防护同一思路：边界清晰）。

## 5. JSON vs CSV：给谁用？

| 格式 | 适合 | 注意 |
|------|------|------|
| JSON | 程序、API、嵌套字段 | 数组/对象好表达 |
| CSV | Excel、运营、简单表格 | 逗号/引号/换行要转义；嵌套要拍平 |

今日 `Contact` 是扁平字段，CSV 很自然。若字段是 `tags: list[str]`，导出时常 `;` 拼接或拆多列——练习里用 `";".join(tags)`。

Python 标准库 `csv` 模块会处理引号转义，**不要手写 `",".join`** 除非字段保证无逗号。

## 6. complete_fn 注入（可测性）

```python
CompleteFn = Callable[[list[dict[str, str]]], str]
# messages → 模型回复文本
```

测试 / Demo 传入 mock；线上再换成真实 Chat Completions。  
这和前端把 `fetch` 抽成可注入依赖一样：不测网络，测编排。

## 7. 和明天的关系

Day 30 周挑战：**会议纪要结构化**（决议 + action items）。  
今天的批处理骨架可以直接复用：把 `Contact` 换成 `MeetingMinutes`，导出字段换成负责人/截止日期即可。

## 8. 纸上 2 分钟

给定 3 段文本，其中第 2 段缺姓名导致校验失败。问：

- `batch_summary` 的 `ok` / `failed` 应是多少？
- CSV 里应有几行数据行（不含表头）？

答案：ok=2, failed=1；CSV 数据行 2 行。
