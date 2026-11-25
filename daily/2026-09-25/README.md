# Day 46｜ReAct 与 Agent Loop

> 日期：2026-09-25（周五）  
> Phase 3 / Week 10 · 学习日序号：**D46 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 用一句话说清 **ReAct**：Reason（想）→ Act（做）→ Observe（看）→ 再想……直到给出最终答案
2. 把 Week 9 的「至多一轮工具」升级成 **while 循环**：只要模型还带 `tool_calls`，就执行、回填、再问
3. 手写最小 `run_agent_loop`，能跑通 **多步**（≥2 轮工具）再收尾
4. 知道 `max_steps` 为什么必须有（防死循环），细节留给 Day 47 打磨

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 10 · D46）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾周挑战：[`../2026-09-24/notes.md`](../2026-09-24/notes.md)

重点抓住三件事：

- **心智模型是 ReAct，协议仍是 Tool Calling**：Thought ≈ content；Action ≈ tool_calls；Observation ≈ role=tool
- **Loop 比单回合只多一个 while**：终止条件 = 无 tool_calls（最终回答）或触顶 max_steps
- **先手写再框架**：今天不用 LangChain / 任何 Agent SDK

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain / pydantic。

### 任务

1. 完成 `exercise/agent_loop.py` 中的 TODO（`tools.py` **已给齐**，勿改接口）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-09-25/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --direct
python3 main.py --max-steps-demo
python3 main.py --trace
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] `run_agent_loop`：无工具时一步 `final_answer`；多步工具后也能收尾
- [ ] 触顶 `max_steps` 时 `stopped_reason == "max_steps"`，进程不崩
- [ ] 入参 `messages` 历史由函数内部维护；不修改调用方传入的无关对象
- [ ] 全程标准库；工具箱只有 `lookup` + `calculate`

---

## 参考实现

先自己做。卡住超过 25 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能徒手画出：Thought → Action → Observation → … → Final Answer
- [ ] 我能指出：Day 45 的「一轮回填」在今天的 loop 里对应**其中一次**迭代
- [ ] 我知道为什么必须有 `max_steps`（费用、延迟、死循环）
- [ ] 我已知明天 Day 47：把终止条件与步数限制做得更严谨

---

## 本周预告（Week 10）

| Day | 主题 |
|-----|------|
| **46** | **ReAct 与 Agent Loop（今天）** |
| 47 | 终止条件与步数限制 |
| 48 | 工具错误恢复 |
| 49 | 轨迹日志 Trace |
| 50 | 周挑战：只读文件助手 |

---

## 通知摘要（便于推送）

**Day 46｜ReAct 与 Agent Loop**  
把手写 while 循环接上 Tool Calling：多步 Reason→Act→Observe，直到最终回答或触顶 max_steps。  
路径：`daily/2026-09-25/`
