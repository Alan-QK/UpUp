# Day 54｜流式事件与工具状态

> 日期：2026-10-07（周三）  
> Phase 3 / Week 11 · 学习日序号：**D54 / 120**  
> 建议时长：**75 分钟**（概念 20 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 区分 **Trace（事后回放）** 与 **流式事件（实时 UI 信号）**
2. 在工具执行前后发出 `tool_start` / `tool_end` 事件
3. 用事件推导前端可消费的工具状态：`pending` → `running` → `ok` / `error`
4. 说出：产品化 Agent 聊天窗为什么必须有这些事件，而不只靠最终文本

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 11 · D54）
2. 今日笔记：[`notes.md`](./notes.md)
3. 对照回顾：[`../2026-09-30/notes.md`](../2026-09-30/notes.md)（Day 49 Trace）

重点抓住三件事：

- **Trace ≠ Stream**：一个偏调试回放，一个偏产品交互
- **成对事件**：`tool_start` 与 `tool_end` 必须配对，前端才能关 spinner
- **状态是派生的**：UI 状态从事件流推导，不要另起一套随意布尔值

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 langchain / langgraph / openai。

### 任务

1. 完成 `exercise/streaming_events.py` 中的 TODO（事件模型 + StreamingRunner）
2. `mini_framework.py` / `tools_builtin.py` / `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-10-07/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --goal "查一下 alpha，再算 7*3"
python3 main.py --timeline
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] 每次工具调用发出配对的 `tool_start` → `tool_end`
- [ ] `tool_end.status` 为 `ok` 或 `error`（ERROR: 前缀判错）
- [ ] `derive_tool_statuses` 能从事件流得到前端状态列表
- [ ] `render_event_timeline` 输出可读时间线
- [ ] 全程标准库（不改 `AgentRunner` 内核；今日写 Streaming 包装层）

---

## 参考实现

先自己做。卡住超过 15 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能一句话说清 Trace 与 Stream 的产品场景差异
- [ ] 我知道前端为何不能只等 Final Answer 才更新工具卡片
- [ ] 我能解释：漏发 `tool_end` 会让 UI 卡在 loading
- [ ] 我已知明天 Day 55：手写 vs 框架对比周挑战
