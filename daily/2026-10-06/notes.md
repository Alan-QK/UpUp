# Day 53 笔记｜自定义工具接入框架（扩展点）

## 1. 今天学什么？

Day 52 你已经有了迷你框架：`Tool` / `ToolRegistry` / `AgentRunner`。  
今天只做一件事：**在不改 Loop 内核的前提下，新增 1 个业务工具**。

| 不要做 | 要做 |
|--------|------|
| 为了新功能去改 `while` Loop | 写 handler → meta → `register` |
| 把业务规则写进超长 system prompt | 规则落地在工具函数 + schema |
| 一次加 5 个工具 | **只加 1 个**，走通扩展路径 |

## 2. 前端迁移直觉

| 你熟悉的前端 | 今天的工具扩展 |
|--------------|----------------|
| 注册一个新的 API route / service | `registry.register(tool)` |
| OpenAPI / TS 类型描述接口 | `parameters` JSON Schema |
| 业务逻辑放 service，不放 router | handler 放业务，Runner 只调度 |
| 插件 / 微前端挂载点 | **Registry = 挂载点** |

结论：框架的扩展点通常是「注册表」，不是「把 if-else 写进核心循环」。

## 3. 业务工具四件套

对接任何 Agent 框架，新工具几乎都要这四样：

```text
1. handler(order_id) -> str     # 真干活
2. description                   # 给人/模型看「何时该用」
3. parameters (JSON Schema)      # 参数名、类型、required
4. register(registry)            # 挂进白名单
```

少任何一件都会出问题：

| 缺什么 | 典型症状 |
|--------|----------|
| handler | 能「选中」工具但执行炸 |
| description | 模型乱调用或从不调用 |
| parameters / required | 参数名对不上，Observation 全是 ERROR |
| register | schema 列表里没有它，等于不存在 |

## 4. 今日业务场景：订单查询

模拟一个电商后台只读接口：

- 工具名：`order_lookup`
- 入参：`order_id`（如 `ORD-1001`）
- 出参：人类可读摘要（状态、金额、收货城市）
- 未知订单：抛错 / 返回 `ERROR:`（由 Registry 统一包装也可）

为什么选这个？

- 前端同学熟悉「订单详情页」数据形状
- 只读、副作用小，适合 Agent 第一批业务工具
- 和已有 `lookup`/`calculate` 正交，不抢职责

## 5. 接入后的数据流（不变）

```text
用户目标
  → Runner while Loop
  → 模型 tool_calls: order_lookup
  → Registry.execute → handler
  → Observation 回填
  → 模型 Final Answer
```

你新增的只是虚线框里的 **handler + schema**；实线框（Runner）昨天已经写完。

## 6. system prompt 要同步

扩展后记得：

1. `registry.names()` 里能看到新名字
2. `openai_tools()` schema 列表含新工具
3. system prompt 点名：何时用 `order_lookup`

否则会出现「代码里注册了，模型却当它不存在」。

## 7. 真实框架里长什么样？（对照预告）

| 迷你框架（今天） | 常见真框架叫法 |
|------------------|----------------|
| `Tool(...)` + `register` | `@tool` / `StructuredTool.from_function` |
| `parameters` dict | Pydantic args schema / JSON Schema |
| `build_business_agent` | `bind_tools` / `create_react_agent(tools=[...])` |

名字不同，扩展心智同一套。

## 8. 常见坑

| 坑 | 症状 | 纠正 |
|----|------|------|
| 在 Runner 里 `if name == "order_lookup"` | 每加工具改核心 | 只 `register` |
| schema 参数名 `id`，handler 要 `order_id` | 一直 TypeError | 名字对齐 |
| 订单库写成全局可变又被测污染 | 测试偶发失败 | 用常量表 / 深拷贝 |
| 未知订单返回空字符串 | 模型胡编状态 | 明确错误信息 |

## 9. 今日一句话

> 会加业务工具，才算真的「会用框架」；只会跑 Demo 工具，只是会抄 README。

## 10. 明日预告

Day 54：流式事件与工具状态——给 UI 输出 `tool_start` / `tool_end` 信号。

---

## 我的记录（请自己填写）

1. 我为 `order_lookup` 写的 description 关键句：  
2. 注册后我用哪两条断言确认扩展成功：  
3. 若接到真实 CRM API，handler 里我会先加哪一层防护：  
