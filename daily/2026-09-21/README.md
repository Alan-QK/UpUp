# Day 43｜单轮 Tool Call 执行

> 日期：2026-09-21（周一）  
> Phase 3 / Week 9 · 学习日序号：**D43 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 读懂助手消息里的 OpenAI 风格 `tool_calls[]`（`id` / `function.name` / `function.arguments`）
2. 把 `arguments` 字符串安全解析成 dict，并按 `name` 路由到本地函数
3. 产出 `role=tool` 的回填消息（含成功与失败两种 `content`）
4. 理解「单轮执行」与完整 Agent Loop 的边界：今天只跑工具，不回头再问模型

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 9 · D43）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾：昨日 Schema [`../2026-09-18/notes.md`](../2026-09-18/notes.md)

重点抓住三件事：

- **协议形状**：模型返回的是「调用意图」，不是直接执行结果
- **执行器职责**：解析 → 校验 → 路由 → 捕获异常 → 字符串化结果
- **消息回填格式**：`tool_call_id` 必须对得上，后面 Day 44 才能继续对话

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain / pydantic。

### 任务

1. 完成 `exercise/tool_executor.py` 中的 TODO
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-09-21/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --json
python3 main.py --fail
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `parse_tool_call` 能解析合法调用，并拦住坏 JSON / 缺字段
- [ ] `default_registry` 含 `get_weather` / `calculate` / `get_current_time`
- [ ] `execute_tool_call` 成功返回 `ok=True`；未知工具 / 执行异常返回 `ok=False` 且 content 可读
- [ ] `execute_assistant_tool_calls` + `to_tool_messages` 能产出标准 `role=tool` 列表
- [ ] 全程标准库（不要引入 langchain / openai SDK）

---

## 参考实现

先自己做。卡住超过 15 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能徒手画出：assistant(`tool_calls`) → executor → tool 消息 的数据流
- [ ] 我知道 `arguments` 为什么是 **字符串**（模型侧 JSON 文本）而不是对象
- [ ] 我能解释未知工具时为何仍要返回 `role=tool`（而不是直接崩溃）
- [ ] 我已知明天 Day 44：把工具结果回填，再问模型生成最终回答

---

## 本周地图（Week 9）

| Day | 主题 |
|-----|------|
| 41 | Chatbot vs Agent |
| 42 | Tool Schema 设计 |
| **43** | **单轮 Tool Call 执行** ← 今天 |
| 44 | 工具结果回填多轮 |
| 45 | 周挑战：双工具 Agent |
