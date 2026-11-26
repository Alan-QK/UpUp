# Day 59｜HITL 确认钩子

> 日期：2026-10-15（周四）  
> Phase 3 / Week 12 · 学习日序号：**D59 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说明 **HITL（Human-in-the-Loop）** 在 Agent 里解决什么问题：危险操作执行前暂停，等人确认
2. 区分三档风险：**safe（自动） / confirm（需确认） / blocked（永不执行）**
3. 实现可注入的 `ConfirmHook`，用脚本化钩子在单测里覆盖批准 / 拒绝 / 超时
4. 把确认结果写成 tool observation，让 Loop 继续（不崩进程），并断言 `confirmations` 轨迹

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 12 · D59）
2. 今日笔记：[`notes.md`](./notes.md)

重点抓住三件事：

- **Guard ≠ HITL**：Guard 拦「能不能调」；HITL 拦「调之前人同不同意」
- **钩子可注入**：生产用 UI/工单审批；单测用 `ScriptedConfirmHook`
- **前端迁移**：危险按钮二次确认 Modal ≈ Agent 的 confirm 节点

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain；**不要**调用真实 LLM。

### 任务

1. 完成 `exercise/hitl_confirm.py` 中的 TODO  
   （风险策略、确认请求/决策、脚本钩子、带 HITL 的 Loop、场景与报告）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-10-15/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --branch safe_auto
python3 main.py --branch approve
python3 main.py --branch reject
python3 main.py --branch timeout
python3 main.py --branch blocked
python3 main.py --report
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] `order_lookup` / `get_time` 为 safe：不触发确认，直接执行
- [ ] `refund_order` / `delete_account` 为 confirm：执行前调用钩子
- [ ] 批准 → 真正执行 handler；拒绝 / 超时 → 观察含 `rejected` / `timeout`，不执行副作用
- [ ] `shell_exec` 等为 blocked：不询问用户，直接 DENIED
- [ ] `AgentResult.confirmations` 记录每次确认请求与决策
- [ ] `render_hitl_report` 含规定二级标题
- [ ] 全程标准库

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能讲清：白名单 Guard 与 HITL 确认各自防什么
- [ ] 我知道哪些操作该标 confirm（退款、删号、发邮件给全员…）
- [ ] 我能用 ScriptedConfirmHook 在单测里钉死批准 / 拒绝 / 超时
- [ ] 我已知明天 Day 60：里程碑 `tool-agent` 验收

---

## 本周预告（Week 12）

| Day | 主题 |
|-----|------|
| 56 | Prompt Injection 案例集 |
| 57 | 工具白名单与参数校验 |
| 58 | Mock LLM 单测 |
| **59** | **HITL 确认钩子（今天）** |
| 60 | 里程碑：`tool-agent` 验收 |

---

## 通知摘要（便于推送）

**Day 59｜HITL 确认钩子**  
给危险工具加执行前确认：safe 自动跑、confirm 等人批、blocked 永不执行；用脚本钩子单测批准/拒绝/超时。  
路径：`daily/2026-10-15/`
