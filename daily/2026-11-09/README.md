# Day 69｜状态机视角

> 日期：2026-11-09（周一）  
> Phase 4 / Week 14 · 学习日序号：**D69 / 120**  
> 建议时长：**80 分钟**（理论 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 用有限状态机（FSM）描述 Agent 的 Plan / Execute / Reflect / HITL 生命周期
2. 分清「状态」与「事件」，并把 Day 68 四态决策映射为转移事件
3. 实现带非法转移校验与 HITL 挂起恢复的 `AgentStateMachine`
4. 从同一份转移表渲染 Mermaid 状态图，并输出学习报告

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-04-memory-multiagent.md`](../../curriculum/phases/phase-04-memory-multiagent.md)（Week 14 · D69）
2. 今日笔记：[`notes.md`](./notes.md)
3. 昨日回顾：[`../2026-11-06/notes.md`](../2026-11-06/notes.md)（四态决策如何变成事件）

重点抓住三件事：

- **状态是「在哪」，事件是「发生了什么」**
- **转移表驱动跳转；非法转移要失败**
- **图必须由同一份转移表生成**

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**调用 LLM。

### 任务

1. 完成 `exercise/state_machine.py` 中的 TODO  
   （转移表 / 跳转 / HITL 恢复 / 情景模拟 / Mermaid 图 / 报告）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-11-09/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --case happy
python3 main.py --case retry
python3 main.py --diagram
python3 main.py --report
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] 合法路径：`idle → planning → executing → reflecting → done`
- [ ] `decision_retry` / `decision_revise` / `decision_abort` 跳转正确
- [ ] HITL：挂起时记录 resume，批准后回到预定状态；拒绝 → `aborted`
- [ ] 非法转移抛错；`render_mermaid` 含所有默认转移
- [ ] `render_state_machine_report` 含规定二级标题
- [ ] 全程标准库

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能解释：状态机比「深层 if-else」解决了什么
- [ ] 我能默写 7 个核心状态与主路径
- [ ] 我知道 Day 68 的 accept/retry/revise/abort 如何变成事件
- [ ] 我已知明日 Day 70：周挑战——多步研究任务

---

## 本周预告（Week 14 · 规划与反思）

| Day | 主题 |
|-----|------|
| 66 | 任务分解 Planner |
| 67 | Plan-and-Execute |
| 68 | Reflection / 自评纠错 |
| **69** | **状态机视角看 Agent（今天）** |
| 70 | 周挑战：多步骤研究任务 |

---

## 通知摘要（便于推送）

**Day 69｜状态机视角**  
把 Plan / Execute / Reflect / HITL 收成可测试的转移表，并画出 Agent 状态图。  
路径：`daily/2026-11-09/`
