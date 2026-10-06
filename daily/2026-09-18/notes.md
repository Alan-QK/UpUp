# Day 42 笔记｜Tool Schema 设计

## 1. 今天学什么？

Day 41 分清了 Chatbot / Agent。Agent 要「做事」，第一步是把能力写成模型能读懂的 **工具契约（Tool Schema）**。

Day 28 练过「从 Python 函数自动反射生成 schema」。今天换视角：**先当产品设计师**，手写 3 个高质量工具定义——名字、描述、参数怎么写，直接决定模型会不会乱调工具。

```text
业务能力（天气 / 计算 / 时间）
  → 手写 OpenAI tools[] 契约
    → 校验结构 + 设计规则
      →（明天 D43）解析 tool_call 并真正执行
```

前端类比：

| 前端 | 今天 |
|------|------|
| 组件 props + JSDoc / Zod | tool `parameters` + description |
| API 路由命名约定 | `snake_case` 动词_名词 |
| OpenAPI 文档质量 | description 写「何时用 / 不何时用」 |

## 2. 模型看到的契约长什么样？

一条工具在 Chat Completions 里通常是：

```json
{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "查询指定城市的当前天气。用户问气温、是否下雨、穿衣建议且需要真实天气数据时使用。",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "城市名，如 Shanghai 或 上海"
        },
        "unit": {
          "type": "string",
          "enum": ["celsius", "fahrenheit"],
          "description": "温度单位；未指定时由实现默认 celsius"
        }
      },
      "required": ["city"]
    }
  }
}
```

要点：

- 顶层 `type` 固定为 `"function"`
- `parameters` 永远是 **object**（参数打包成一个对象）
- `required` ⊆ `properties` 的键
- 可选参数用「有默认 / 可不传」表达，不要塞进 required

## 3. 设计原则（今日练习会编码校验）

| 原则 | 好 | 坏 |
|------|----|----|
| 命名 | `get_weather`、`calculate`、`get_current_time` | `doStuff`、`tool1`、`Weather` |
| 描述 | 说明**何时调用**、边界 | 只写「天气工具」三个字 |
| 参数 | 少而精；枚举约束单位/格式 | 一个 `data: object` 包天下 |
| 职责 | 一工具一事 | `get_weather_and_send_email` |
| 安全 | 描述里标明只读 / 无副作用 | 含糊到像能改世界 |

**命名规则（今日约定）：**

- 仅小写字母、数字、下划线
- 必须以字母开头
- 长度 3–64
- 推荐 `动词_名词`（`get_*` / `calculate` / `list_*`）

**描述规则（今日约定）：**

- 去掉首尾空白后长度 ≥ 20
- 建议包含「何时使用」线索（练习里用关键词启发式即可）

## 4. 今日三个工具（Phase 3 Week 9 主线）

| 工具名 | 用途 | 关键参数 | 副作用 |
|--------|------|----------|--------|
| `get_weather` | 查城市天气 | `city` 必填；`unit` 可选 enum | 无（只读） |
| `calculate` | 算术表达式求值 | `expression` 必填 | 无（本地计算） |
| `get_current_time` | 取当前时间 | `timezone` 可选 | 无（只读） |

为什么选这三个？

1. 覆盖「外部事实 / 本地计算 / 系统信息」三类常见工具形态  
2. 都是只读，适合先学协议，再学危险工具与 HITL（D50 / D59）  
3. 周五周挑战（D45）会把它们拼成双工具 Agent

## 5. 和 Day 28 的差别

| | Day 28 | Day 42（今天） |
|--|--------|----------------|
| 输入 | 已有 Python 函数 | 空白画布，你来设计 |
| 动作 | `inspect` 反射生成 | 手写 dict + 设计校验 |
| 目标 | 会生成契约 | 会写出**好**契约 |

反射生成保证结构正确；设计功力保证模型**用得对**。两边都要。

## 6. 常见翻车

1. **名字含糊**：`helper` → 模型不知道何时调  
2. **描述像内部注释**：写实现细节，不写用户意图触发条件  
3. **参数过宽**：`payload: object` → 等于没 schema  
4. **required 写错**：把可选字段塞进 required，或 required 里出现不存在的键  
5. **工具重叠**：`get_weather` 和 `get_forecast` 边界不清 → 模型乱选

## 7. 今日一句话

> Tool Schema 是 Agent 的 API 文档：写清楚名字、何时调用、传什么——模型才会稳定地「动手」。

## 8. 明日预告

Day 43：单轮 Tool Call 执行——解析模型返回的 `tool_calls`，按 name 路由到本地函数并执行。

---

## 我的记录（请自己填写）
