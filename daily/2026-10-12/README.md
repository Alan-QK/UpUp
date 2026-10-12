# Day 57｜工具白名单与参数校验

> 日期：2026-10-12（周一）  
> Phase 3 / Week 12 · 学习日序号：**D57 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说明为什么「模型想调用工具」≠「系统必须执行」——中间要有**硬门禁**
2. 用**允许列表（allowlist）**限制可调用工具名，拒绝未知 / 禁用工具
3. 按简易 JSON Schema 校验参数类型、必填与枚举，失败时给出可读错误
4. 把 Day 56 的注入案例接到「就算模型被忽悠，危险工具也调不起来」

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 12 · D57）
2. 今日笔记：[`notes.md`](./notes.md)

重点抓住三件事：

- **白名单 vs 黑名单**：Agent 安全默认「没登记就不给调」
- **参数校验在 handler 之前**：坏参数不应进入业务逻辑
- **门禁是确定性代码**：不依赖模型「自觉」，才接得住注入

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain；**不要**调用真实 LLM。

### 任务

1. 完成 `exercise/tool_guard.py` 中的 TODO  
   （允许列表、Schema 校验、授权决策、受护调用、防护报告）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-10-12/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --call order_lookup --args '{"order_id":"ORD-1001"}'
python3 main.py --call shell_exec --args '{"cmd":"rm -rf /"}'
python3 main.py --report
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] `build_default_allowlist` 含 `order_lookup` / `get_time`，不含危险工具名
- [ ] 未知工具名 → `deny`，原因含 `allowlist` 或 `unknown`
- [ ] 缺必填 / 类型错 / 枚举越界 → `deny`，原因可读
- [ ] 合法调用 → `allow`，`guarded_invoke` 能返回业务结果
- [ ] `render_guard_report` 含规定二级标题
- [ ] 全程标准库

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能用前端类比讲清：白名单 ≈ CSP allowlist / API 网关鉴权
- [ ] 我知道「提示词里写禁止」挡不住注入，硬校验才能兜底
- [ ] 我能指出校验应发生在 handler 之前的哪一层
- [ ] 我已知明天 Day 58：用 Mock LLM 给 Agent 写单测

---

## 本周预告（Week 12）

| Day | 主题 |
|-----|------|
| 56 | Prompt Injection 案例集 |
| **57** | **工具白名单与参数校验（今天）** |
| 58 | Mock LLM 单测 |
| 59 | HITL 确认钩子 |
| 60 | 里程碑：`tool-agent` 验收 |

---

## 通知摘要（便于推送）

**Day 57｜工具白名单与参数校验**  
给工具调用加硬门禁：允许列表 + Schema 参数校验；模型想调未登记或参数非法的工具一律 deny。  
路径：`daily/2026-10-12/`
