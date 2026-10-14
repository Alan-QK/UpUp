# Day 58 笔记｜Mock LLM 单测

## 1. 一句话定义

**Mock LLM 单测**：不调用真实模型，用**预设的 assistant 消息序列**驱动 Agent Loop，在本地用 pytest 验证关键控制流是否正确。

## 2. 为什么必须 Mock

| 真实 LLM | Mock LLM |
|----------|----------|
| 非确定性（同一 prompt 多次结果不同） | 完全确定 |
| 要密钥、要网络、要花钱 | 零密钥、离线、免费 |
| 难覆盖「拒绝 / 触顶」等边角 | 想测哪条分支就脚本哪条 |
| CI 易 flaky | CI 稳定绿灯 |

结论：测的是 **你的编排代码**（Loop / Guard / 消息拼接），不是测模型智商。

## 3. 前端迁移直觉

| 你熟悉的前端测试 | Agent 侧对应 |
|------------------|--------------|
| `vi.mock('fetch')` / MSW | `MockLLM` / `ScriptedChat` |
| 断言 store 状态与 UI | 断言 `stopped_reason`、messages、观察文本 |
| 测 loading / error / success 三态 | 测 final / tool_ok / deny / max_steps |
| 不测第三方 CDN 内部实现 | 不测 tokenizer / 厂商 SDK 内部 |

## 4. 昨天（Day 57）→ 今天

Day 57 做出了硬门禁：未知工具 / 坏参数 → `deny`。  
今天要证明：**这些分支在 Agent Loop 里真的被走到、且可被测试钉死**。

```text
用户 goal
   ↓
MockLLM 吐出 assistant（可能含 tool_calls）
   ↓
Guard（Day 57 同款逻辑，今日内嵌迷你版）
   ├─ allow → 执行 handler → observation
   └─ deny  → 把拒绝原因写进 observation（不炸进程）
   ↓
再问 MockLLM … 直到 final 或 max_steps
```

## 5. 关键分支清单（今日必覆盖）

| 分支 ID | 脚本行为 | 期望 |
|---------|----------|------|
| `final` | 第一条就是最终回答 | `final_answer`，无 tool 观察 |
| `tool_ok` | 合法 `order_lookup` → 再终答 | 观察含订单；`final_answer` |
| `deny` | 调 `shell_exec` → 再终答 | 观察含 denied；未执行危险逻辑 |
| `max_steps` | 每步都调工具且步数触顶 | `max_steps` |
| `bad_args` | `order_lookup` 缺 `order_id` | 观察含 denied / missing |

## 6. 断言怎么写才稳

**稳：**

- `result.stopped_reason == "final_answer"`
- `"ORD-1001" in observation_content`
- `"denied" in observation_content.lower()`
- `len(mock.calls) == 2`

**不稳（避免）：**

- 断言模型「Thought」的完整原文措辞
- 依赖真实 API 延迟或 token 数

## 7. 今日练习模块

| 模块 | 作用 |
|------|------|
| `MockLLM` | 按序吐 assistant；记录每次 messages 深拷贝 |
| `assistant_final` / `assistant_tool_call` | 测试夹具工厂 |
| `build_default_allowlist` + `guarded_execute` | 迷你 Guard + 执行器 |
| `run_guarded_agent` | 最小 Loop |
| `scenario_*` | 四条标准脚本场景 |
| `render_coverage_report` | 单测覆盖说明 Markdown |

## 8. 常见坑

| 坑 | 症状 | 纠正 |
|----|------|------|
| Mock 耗尽未处理 | Loop 中途 `RuntimeError` | 脚本条数 ≥ 预期模型调用次数 |
| deny 时直接抛到测试外 | 进程崩、难断言 | 写成 tool observation，让 Loop 继续 |
| 只测 happy path | 线上 Guard 形同虚设 | 至少加 deny + max_steps |
| 共享可变 Mock 状态 | 用例互相污染 | 每个 test 新建 `MockLLM` |

## 9. 今日一句话

> 能被 Mock 驱动并断言的分支，才算你真正拥有的 Agent 行为。

## 10. 明日预告

Day 59：HITL 确认钩子——危险操作在执行前暂停，等待用户确认 / 拒绝。

---

## 我的记录（请自己填写）

1. 我项目里最该先用 Mock 钉死的一条分支：  
2. 我准备断言的 3 个字段：  
3. 一条我想写进 code review 的测试要求：  
