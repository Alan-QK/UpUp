# Day 57 笔记｜工具白名单与参数校验

## 1. 一句话定义

**工具白名单 + 参数校验**：在 Agent 真正执行工具之前，用确定性代码回答两件事——

1. **这个工具名允不允许调？**（allowlist）
2. **参数形状对不对？**（schema validation）

过不了门禁 → 直接 `deny`，根本不进 handler。

## 2. 前端迁移直觉

| 你熟悉的前端 / 网关 | Agent 侧对应 |
|---------------------|--------------|
| CSP：只允许加载列出的脚本源 | 工具 allowlist：只允许列出的 tool name |
| API 网关校验 JWT + body schema | Guard 层校验调用方意图落地前的 args |
| TypeScript 类型 + Zod / yup | 简易 JSON Schema：type / required / enum |
|「按钮灰掉」≠ 后端鉴权 |「Prompt 里写禁止」≠ 执行层拒绝 |

结论：安全边界必须落在 **执行路径上的硬代码**，不能只写在给模型看的提示词里。

## 3. 昨天（Day 56）→ 今天

Day 56 证明：注入可以把模型忽悠去「想」调用危险动作。  
今天补硬约束：就算模型输出了 `shell_exec` 或乱参数——

```text
LLM 提议 tool_call
        ↓
   Guard（今日）
   ├─ name ∈ allowlist？
   ├─ args 过 schema？
   └─ 否 → deny（记录原因）
        ↓ 是
   handler（业务）
```

启发式检测（Day 56）挡「话术」；白名单（今天）挡「动作」。两层都要。

## 4. Allowlist 设计要点

| 原则 | 做法 |
|------|------|
| 默认拒绝 | 未登记 = 禁止，不要「除了坏的都允许」 |
| 显式启用 | 每个工具有 `enabled`；可临时关掉而不删 schema |
| 最小权限 | 客服 Agent 只要 `order_lookup` / `get_time`，不要给文件系统 |
| 名称规范化 | strip + lower，避免 `Order_Lookup` 绕过 |

危险示意（**绝不进今日默认允许列表**）：`shell_exec`、`http_fetch_any`、`read_secrets`。

## 5. 参数校验（教学用迷你 Schema）

今日练习支持的字段（够用即可，不是完整 JSON Schema 实现）：

```json
{
  "type": "object",
  "properties": {
    "order_id": { "type": "string", "minLength": 1 },
    "unit": { "type": "string", "enum": ["s", "ms"] }
  },
  "required": ["order_id"],
  "additionalProperties": false
}
```

校验顺序建议：

1. args 必须是 `dict`
2. 补齐 / 检查 `required`
3. 若 `additionalProperties=false`，拒绝多余键
4. 逐字段检查 `type` / `enum` / `minLength`

失败信息要**人类可读**（含字段名），方便写进 trace 与单测断言。

## 6. 今日练习模块

| 模块 | 作用 |
|------|------|
| `ToolSpec` | 工具名、描述、schema、enabled、handler |
| `build_default_allowlist` | 安全默认：订单查询 + 取时间 |
| `validate_args` | 按 schema 产出 ok / 错误列表 |
| `authorize_tool_call` | allow / deny 决策 |
| `guarded_invoke` | 先授权再调用；deny 时抛错或返回结构化失败 |
| `render_guard_report` | 一页 Markdown 防护说明 |

## 7. 常见坑

| 坑 | 症状 | 纠正 |
|----|------|------|
| 只在 Prompt 写「禁止 shell」 | 注入后仍输出 shell 调用 | Guard 层硬拒绝未登记名 |
| 校验放在 handler 内部 | 部分路径忘记校验 | 统一在 `guarded_invoke` 入口 |
| 黑名单思维 | 总有新危险名漏网 | 改用 allowlist |
| 错误信息太模糊 | 调试与测试难断言 | 固定前缀：`unknown tool` / `missing` / `type` / `enum` |

## 8. 今日一句话

> 模型可以「提议」任何工具调用；系统只「执行」白名单里、且参数合法的那一部分。

## 9. 明日预告

Day 58：Mock LLM 单测——用假模型驱动 Agent Loop，覆盖「合法调用 / 被 Guard 拒绝 / 达到 max_steps」等分支。

---

## 我的记录（请自己填写）

1. 我当前项目里最危险、却可能被模型点到的工具：  
2. 我准备放进 allowlist 的最小集合：  
3. 一条我想写进 code review checklist 的校验规则：  
