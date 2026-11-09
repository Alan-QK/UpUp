# Day 45｜周挑战：双工具 Agent

> 日期：2026-09-24（周四）  
> Phase 3 / Week 9 · 学习日序号：**D45 / 120**  
> 建议时长：**90 分钟**（概念 20 + Coding 65 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 把 Week 9 积木（Schema → 执行器 → 回填）**拼成可演示的最小 Agent**
2. 只接入两个工具：`calculate` + `get_current_time`，说清「工具箱白名单」为什么重要
3. 用离线 `HeuristicChat`（或注入的 `ScriptedChat`）跑通：用户提问 → tool_calls → 执行 → 回填 → 最终回答
4. 分清：今天是「单回合双工具」周挑战；真正的多步 ReAct Loop 从 Day 46 开始

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 9 · D45）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾：[`../2026-09-18/notes.md`](../2026-09-18/notes.md)～[`../2026-09-23/notes.md`](../2026-09-23/notes.md)

重点抓住三件事：

- **周挑战心态**：不引入新框架，把 D42–D44 串起来交付 Demo
- **双工具够用**：时间 + 计算器覆盖「查事实 / 做运算」两类侧效应
- **启发式模型**：练习用 `HeuristicChat` 离线可测；真机再换成真实 Chat Completions

---

## Coding 练习（65 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain / pydantic。

### 任务

1. 完成 `exercise/dual_agent.py` 中的 TODO（`toolkit.py` / `roundtrip.py` **已给齐**，勿改接口）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-09-24/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --calc "帮我算 12*(3+4)"
python3 main.py --time "现在 Asia/Shanghai 几点？"
python3 main.py --both
python3 main.py --chat "你好呀"
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] `plan_tool_calls`：可单独/同时发出 `calculate` 与 `get_current_time`
- [ ] `HeuristicChat`：第一轮规划工具，第二轮根据 tool 结果合成回答；无需工具时直接回答
- [ ] `run_dual_agent`：拼好 system+user，走一轮 `run_tool_roundtrip`，返回 `AgentResult`
- [ ] 工具箱只有这两个名字（白名单）；全程标准库

---

## 参考实现

先自己做。卡住超过 25 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能徒手画出：user → assistant(tool_calls×1..2) → tool* → assistant(final)
- [ ] 我知道为什么周挑战只给两个工具（边界清晰、可演示、可测）
- [ ] 我能解释 `HeuristicChat` 与真实 LLM 的替换点（同一 `ChatFn` 签名）
- [ ] 我已知下周 Day 46：手写 ReAct / Agent Loop（多步，直到停）

---

## 本周收口（Week 9）

| Day | 能力 |
|-----|------|
| 41 | Chatbot vs Agent |
| 42 | Tool Schema 设计 |
| 43 | 单轮 Tool Call 执行 |
| 44 | 工具结果回填多轮 |
| **45** | **双工具 Agent（周挑战）** |

下周进入 **手写 Agent Loop**：ReAct、max_steps、错误恢复、轨迹日志。

---

## 通知摘要（便于推送）

**Day 45｜周挑战：双工具 Agent**  
串起 Schema / 执行器 / 回填，交付「时间 + 计算器」最小可用 Agent Demo（离线可测）。  
路径：`daily/2026-09-24/`
