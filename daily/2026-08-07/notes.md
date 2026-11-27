# Day 14 笔记｜Token 与成本意识

## 一句话

**Token 是 LLM 的计量单位；每次调用都要会记账——用量从哪来、钱怎么算、日志怎么打。**

---

## Token 是什么？

模型读入/写出的不是「字符」或「单词」，而是 **token**（子词片段）。

| 文本类型 | 粗直觉（非精确） |
|----------|------------------|
| 英文 | 大约 4 个字符 ≈ 1 token |
| 中文 | 常常接近 **1 个汉字 ≈ 1 token** |
| 代码 / 标点 | 视分词器而定，波动大 |

精确值只有 **模型方的 tokenizer**（或响应里的 `usage`）说了算。  
本地估算是为了：**没拿到 usage 时仍能做预算；有 usage 时用来对账。**

前端类比：浏览器 Performance 里有「估算」和「真实导航计时」——今天你要同时会算这两种。

---

## 响应里的 `usage` 字段

非流式 Chat Completions（Day 11）常见形态：

```json
{
  "usage": {
    "prompt_tokens": 120,
    "completion_tokens": 45,
    "total_tokens": 165
  }
}
```

- **prompt_tokens**：输入侧（system + 历史 + 本轮 user 等）
- **completion_tokens**：模型吐出的内容
- **total_tokens**：通常等于两者之和（以服务端为准）

流式（Day 13）默认 chunk 里常常**没有** usage；要额外开 `stream_options` 或结束后另查。  
所以记账逻辑最好：**优先 API usage，缺失再本地估算。**

---

## 费用怎么算？

厂商按 **百万 token** 报价，且 **输入/输出单价不同**（输出通常更贵）：

```text
cost_usd =
  prompt_tokens     / 1_000_000 * input_usd_per_1m
+ completion_tokens / 1_000_000 * output_usd_per_1m
```

今日练习用一张**示意价目表**（不是实时官网价），重点练公式与记账，不背具体数字。

Agent 场景为什么更贵？

```text
一轮用户问题
  → 可能多次模型调用（规划 / 工具后总结 / 反思）
  → 历史越聊越长 → prompt_tokens 膨胀
  → 工具 JSON 也占上下文
```

成本意识 = 少废话上下文 + 控制步数 + 能观测。

---

## 今日约定的估算规则（练习用）

为了单测稳定，采用**确定性启发式**（不是 tiktoken）：

1. 空字符串 → `0`
2. 逐字符扫描：
   - CJK 类字符（汉字等）→ 各计 **1** token
   - 其余字符合计 `n` → `(n + 3) // 4`（即向上按 4 字符一档）
3. 两者相加

例：

- `"你好"` → 2  
- `"abcd"` → 1  
- `"abcdefgh"` → 2  
- `"你好abcd"` → 2 + 1 = 3  

有真实 API 时：**以 `usage` 为准**；估算只做兜底与课前预算。

---

## 用量账本（UsageLedger）

建议最小能力：

1. `record(...)`：写入一条 `UsageRecord`（model / tokens / cost / source）
2. `record_from_api_usage(...)`：两边 token 都有 → `source="api"`；否则用文本估算补齐 → `source="estimate"`
3. `record_from_texts(...)`：纯本地估算
4. `format_log_line` / `format_summary`：人能读、也能 grep

日志行约定（今日练习）：

```text
usage model=gpt-4o-mini prompt=12 completion=8 total=20 cost_usd=0.00000660 source=api
```

`cost_usd` 保留 **8** 位小数。

---

## 和前后日的关系

```text
Day 11  拿到 usage 字段
Day 12  多轮 → prompt 变长
Day 13  流式体验（usage 常缺失）
Day 14  记账 / 估算 / 费用日志   ← 今天
Day 15  周挑战：多轮 CLI（可把 ledger 挂上去）
```

---

## 常见坑

1. **只盯着 completion**：多轮里 prompt 才是大头  
2. **把估算当账单**：结算以服务商 usage / 控制台为准  
3. **忽略输出单价更高**：同样 1k token，回复往往比提问贵  
4. **Agent 不限步数**：工具循环能把日预算打穿  

---

## 今日一句话

> 每次调用留一条 usage 日志：有官方用量用官方的，没有就估算；先看见成本，才谈优化。

## 明日预告

Day 15（下周一开始）：周挑战——支持 `/reset` `/exit` 的多轮对话 CLI。
