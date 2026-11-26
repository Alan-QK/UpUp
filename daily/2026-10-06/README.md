# Day 53｜自定义工具接入框架

> 日期：2026-10-06（周二）  
> Phase 3 / Week 11 · 学习日序号：**D53 / 120**  
> 建议时长：**75 分钟**（概念 20 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 按固定步骤把 **1 个业务工具** 接到框架风格的 `ToolRegistry`
2. 写出工具的四件套：`handler` / `description` / `parameters` / `register`
3. 扩展后的 Agent 能在 Loop 里正确调用新工具（`ScriptedChat` mock）
4. 说出扩展点在哪：框架内核不动，业务能力靠「注册」生长

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 11 · D53）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾迷你框架：[`../2026-10-05/notes.md`](../2026-10-05/notes.md)

重点抓住三件事：

- **扩展 ≠ 改 Loop**：新能力进 Registry，不进 Runner
- **业务工具四件套**：可调用函数 + 人话描述 + JSON Schema + 注册调用
- **system prompt 要同步**：模型只「知道」你写进提示/ schema 的工具

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 langchain / langgraph / openai。

### 任务

1. 完成 `exercise/business_tools.py` 中的 TODO（新增 `order_lookup` 业务工具）
2. `mini_framework.py` / `tools_builtin.py` / `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-10-06/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --goal "查一下订单 ORD-1002 的状态"
python3 main.py --checklist
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `order_lookup`：按订单号返回状态摘要；未知订单 → 明确错误
- [ ] `register_business_tools`：把业务工具挂到已有 Registry（保留 lookup/calculate）
- [ ] `build_business_agent`：system prompt 含 `order_lookup`，Runner 能跑通多步
- [ ] `render_extension_checklist` 产出「接入新工具」检查清单
- [ ] 全程标准库（不改 Runner 内核去硬编码业务）

---

## 参考实现

先自己做。卡住超过 15 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能在不改 `AgentRunner` 的前提下加第 4 个工具
- [ ] 我知道 schema 的 `required` 漏写会导致什么运行时问题
- [ ] 我能解释：为什么业务逻辑放在 handler，而不是塞进 system prompt 长文
- [ ] 我已知明天 Day 54：流式事件与工具状态（tool_start / tool_end）
