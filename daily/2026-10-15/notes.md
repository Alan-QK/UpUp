# Day 59 笔记｜HITL 确认钩子

## 1. 一句话定义

**HITL 确认钩子**：Agent 在执行**高风险工具**之前暂停，把「拟执行动作」交给人（或审批系统）做 **批准 / 拒绝 / 超时**，再决定是否真的调用 handler。

## 2. Guard vs HITL（别混）

| 层 | 问的问题 | 典型手段 |
|----|----------|----------|
| Guard（Day 57） | 这个工具/参数**允不允许出现**？ | 白名单、Schema、禁用危险名 |
| HITL（今天） | 即使允许，**现在要不要做**？ | 确认弹窗、工单、双人复核 |
| Mock 单测（Day 58） | 这些分支**能不能被测到**？ | ScriptedConfirmHook + MockLLM |

一句话：

> Guard 管「能不能叫」；HITL 管「叫之前人点没点同意」。

## 3. 三档风险（今日模型）

| 档位 | 含义 | 例子 |
|------|------|------|
| `safe` | 只读/可逆，自动执行 | `order_lookup`、`get_time` |
| `confirm` | 有副作用，需人确认 | `refund_order`、`delete_account` |
| `blocked` | 永不执行（连确认也不给） | `shell_exec`、`rm_rf` |

产品上常见扩展（了解即可）：按金额阈值升档、按角色跳过 confirm、超时默认拒绝。

## 4. 前端迁移直觉

| 你熟悉的前端 | Agent 侧对应 |
|--------------|--------------|
| 删除按钮 → Modal「确认删除？」 | `confirm` 工具 → `ConfirmHook` |
| 表单 `disabled` 提交中 | 等待确认时暂停 Loop，UI 显示「待审批」 |
| 用户点取消 → toast「已取消」 | `reject` → observation `REJECTED_BY_USER` |
| 请求超时 | `timeout` → 当拒绝处理，默认不执行 |

## 5. 钩子为什么要可注入

```text
生产：WebSocket / SSE 推 ConfirmationRequest → 前端 Modal → 回传 approve/reject
单测：ScriptedConfirmHook([approve, reject, ...]) 按序吐决策
Demo：AlwaysApprove / AlwaysReject（教学用，生产慎用 AlwaysApprove）
```

把「等人」抽象成函数，Loop 才可测、可替换渠道（Slack 审批、工单系统…）。

## 6. 今日数据流

```text
MockLLM 吐出 tool_call
        ↓
风险分级 classify_risk(tool)
   ├─ blocked → DENIED（不问人）
   ├─ safe    → 直接 handler
   └─ confirm → ConfirmHook(request)
                  ├─ approve → handler（记副作用）
                  ├─ reject  → REJECTED_BY_USER（无副作用）
                  └─ timeout → CONFIRM_TIMEOUT（无副作用）
        ↓
observation 回填 messages，Loop 继续
```

## 7. 断言什么

**稳：**

- `result.confirmations` 长度与决策字段
- 拒绝/超时后，副作用集合**不含**对应 order_id / account_id
- blocked 工具：`confirmations` 为空（从未询问）
- `stopped_reason == final_answer`

**不稳：**

- 断言确认文案的完整中文措辞
- 依赖真实人工点击

## 8. 今日练习模块

| 模块 | 作用 |
|------|------|
| `classify_risk` / `build_tool_catalog` | 风险表 + 工具目录 |
| `ConfirmationRequest` / `ConfirmationDecision` | 确认协议 |
| `ScriptedConfirmHook` | 单测用按序决策 |
| `hitl_execute` | 分级 + 可选钩子 + 执行 |
| `run_hitl_agent` | 带 HITL 的最小 Loop |
| `scenario_*` | safe / approve / reject / timeout / blocked |
| `render_hitl_report` | Markdown 说明 |

## 9. 常见坑

| 坑 | 症状 | 纠正 |
|----|------|------|
| confirm 工具先执行再问 | 钱已退、号已删 | **先钩子，后 handler** |
| 拒绝时抛异常打断 Loop | 测试难写、前端无续聊 | 写成 observation |
| blocked 也弹确认 | 误导用户「好像能批」 | blocked 直接 deny |
| AlwaysApprove 上生产 | 等于没有 HITL | 仅 Demo；生产接真 UI |
| 副作用用全局可变且用例间共享 | 测试互相污染 | 每场景新建副作用账本 |

## 10. 今日一句话

> 能暂停等人点头的 Agent，才敢接有副作用的工具。

## 11. 明日预告

Day 60：里程碑 `tool-agent`——把 Week 9–12 的 Schema / Loop / Guard / Mock / HITL 收成可演示项目。

---

## 我的记录（请自己填写）

1. 我业务里最该标 `confirm` 的 2 个操作：  
2. 超时默认策略我想选（拒绝 / 升级审批）：  
3. 前端确认 Modal 上我要展示的 3 个字段：  
