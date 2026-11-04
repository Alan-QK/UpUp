# Day 44｜工具结果回填多轮

> 日期：2026-09-23（周三）  
> Phase 3 / Week 9 · 学习日序号：**D44 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清 Tool Calling 的**消息协议**：`user → assistant(tool_calls) → tool* → assistant(最终回答)`
2. 校验 tool 回填是否与 `tool_calls[].id` **一一对应**（缺 id / 多 id / 乱序都要拦）
3. 把「执行结果」拼进 messages 后，**再问一次模型**拿到最终自然语言回答
4. 分清：今天是「单次工具回合 + 收尾回答」，还不是完整的多步 Agent Loop（那是 Day 46）

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 9 · D44）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾：昨日执行器 [`../2026-09-21/notes.md`](../2026-09-21/notes.md)

重点抓住三件事：

- **协议顺序不能乱**：tool 消息必须紧跟带 `tool_calls` 的 assistant
- **`tool_call_id` 是外键**：对不上，模型侧会懵，API 也可能直接报错
- **注入 ChatFn**：真实项目调 HTTP；练习用 `ScriptedChat`，方便单测

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain / pydantic。

### 任务

1. 完成 `exercise/roundtrip.py` 中的 TODO（协议校验 + 消息拼接 + 一轮回填编排）
2. `mini_executor.py` **已给齐**（精简自 Day 43），阅读即可，勿改接口
3. `main.py` **已给齐**，阅读即可
4. 跑通测试：

```bash
cd daily/2026-09-23/exercise
python3 -m pytest -q
```

5. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --json
python3 main.py --mismatch
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `validate_tool_followup`：id 集合与顺序必须与 `tool_calls` 一致
- [ ] `build_messages_after_tools`：返回**新列表**，不修改入参 history
- [ ] `run_tool_roundtrip`：无 tool_calls 时直接收尾；有则执行 → 回填 → 再问模型
- [ ] 第二轮若仍带 `tool_calls` → `ValueError`（今日只做一轮工具）
- [ ] 全程标准库（不要引入 langchain / openai SDK）

---

## 参考实现

先自己做。卡住超过 15 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能徒手画出完整一回合的 messages 数组（含 role / tool_call_id）
- [ ] 我知道为什么失败的 tool 也要回填（而不是从 history 里删掉 assistant）
- [ ] 我能解释 `ScriptedChat.calls` 里第二次请求为何已包含 tool 消息
- [ ] 我已知明天 Day 45：周挑战——把天气/计算/时间串成可演示的双工具 Agent

---

## 本周地图（Week 9）

| Day | 主题 |
|-----|------|
| 41 | Chatbot vs Agent |
| 42 | Tool Schema 设计 |
| 43 | 单轮 Tool Call 执行 |
| **44** | **工具结果回填多轮** ← 今天 |
| 45 | 周挑战：双工具 Agent |
