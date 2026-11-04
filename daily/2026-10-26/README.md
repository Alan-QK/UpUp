# Day 60｜里程碑：tool-agent

> 日期：2026-10-26（周一）  
> Phase 3 / Week 12 · 学习日序号：**D60 / 120**  
> 建议时长：**90 分钟**（概念 15 + Coding 70 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 把 Phase 3 的能力收成一个可演示项目：`projects/tool-agent`
2. 在同一条链路上同时具备：**≥3 工具**、**手写 Loop**、**max_steps**、**Trace 回放**、**Guard 安全**、**HITL 确认**、**Mock 场景验收**
3. 用 MockLLM 离线跑通 pytest（不依赖外网与真实 Chat Key）
4. 对照阶段验收清单，写出一次「坏轨迹」复盘

---

## 学习内容（15 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（**里程碑验收清单**）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选速览：Day 46 Loop / Day 49 Trace / Day 57 Guard / Day 58 Mock / Day 59 HITL

重点抓住三件事：

- **里程碑 ≠ 新概念堆料**：今天是「拼装 + 打磨」
- **编排层要薄**：`ToolAgent` 只负责串联 Guard → HITL → handler → Trace
- **作品要可演示**：`python3 main.py demo` / `scenario` / `report` 必须脚本化跑通

---

## Coding 练习（70 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain。

### 任务

1. 完成 `exercise/tool_agent.py` 中的 TODO（`ToolAgent` 编排层）
2. 其余文件已给齐：`tools` / `guard` / `hitl` / `mock_llm` / `trace` / `main`
3. 跑通测试：

```bash
cd daily/2026-10-26/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py demo
python3 main.py scenario calc_time
python3 main.py scenario refund_reject
python3 main.py scenario blocked_shell
python3 main.py report
```

5. **提交里程碑**：把可运行实现同步到 [`projects/tool-agent/`](../../projects/tool-agent/)（本仓库已提供完整参考副本；你自学时请先做 exercise，再对照 solution / projects）

### 验收标准（对齐 Phase 3）

- [ ] 至少 3 个真实工具（时间 / 计算器 / 只读文件 / 假 HTTP 等）
- [ ] 手写 Agent Loop 可独立运行
- [ ] 有最大步数（`max_steps`）
- [ ] 有 trace 日志（每步可回放）
- [ ] 有基础安全约束（禁止任意 shell、路径越界、危险名）
- [ ] mock 测试覆盖关键路径（含 HITL 批准/拒绝）
- [ ] README 含架构示意（见 `projects/tool-agent/README.md`）
- [ ] `pytest` 全部通过（纯本地）
- [ ] 在 [`notes.md`](./notes.md)「坏轨迹复盘」写下一次观察

---

## 参考实现

先自己做。卡住超过 25 分钟再看：[`solution/`](./solution/)

打磨后的项目位置：[`projects/tool-agent/`](../../projects/tool-agent/)

---

## 自检清单

- [ ] 我能画出：goal → LLM → Guard → HITL → tool → observation → loop → trace
- [ ] 我知道 Guard 与 HITL 各自防什么
- [ ] 我能向同事 3 分钟讲清这个 tool-agent 的能力边界（MockLLM / 假 HTTP / 沙箱只读）
- [ ] Phase 3 结束后，我清楚 Phase 4 将进入记忆与多智能体

---

## 通知摘要（便于推送）

**Day 60｜里程碑：tool-agent**  
打磨可演示 Agent：多工具 + 手写 Loop + Guard + HITL + Trace + Mock 验收；提交 `projects/tool-agent`。  
路径：`daily/2026-10-26/` · 项目：`projects/tool-agent/`
