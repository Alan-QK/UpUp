# Phase 4｜记忆、规划与多智能体

> 周期：Week 13–16（约 20 个工作日）  
> 关键词：Memory、Planning、Reflection、Multi-Agent、HITL

---

## 阶段目标

1. 区分短期记忆、摘要记忆、长期向量记忆并会实现
2. 为复杂任务加入计划-执行-反思
3. 搭建最小多智能体协作（主管/工人或流水线）
4. 交付里程碑：`projects/research-crew`

---

## 周计划

### Week 13 · 记忆系统

| Day | 主题 | Coding |
|-----|------|--------|
| D61 | 会话记忆与窗口策略 | 复用 Phase1 |
| D62 | 对话摘要记忆 | summarize 压缩 |
| D63 | 长期记忆（向量） | 用户偏好存储 |
| D64 | 记忆读写策略 | 何时记/何时取 |
| D65 | 周挑战：带记忆的个人助理 | 跨会话回忆 |

### Week 14 · 规划与反思

| Day | 主题 | Coding |
|-----|------|--------|
| D66 | 任务分解 | planner 模块 |
| D67 | Plan-and-Execute | 执行器 |
| D68 | Reflection / 自评纠错 | critic 步 |
| D69 | 状态机视角看 Agent | 状态图草图 |
| D70 | 周挑战：多步骤研究任务 | 计划可展示 |

### Week 15 · 多智能体入门

| Day | 主题 | Coding |
|-----|------|--------|
| D71 | 何时需要 Multi-Agent | 决策清单 |
| D72 | 流水线：Research → Write | 两 Agent |
| D73 | 主管-工人模式 | router |
| D74 | 共享黑板 / 消息总线 | 简单总线 |
| D75 | 周挑战：三角色协作 | 三 Agent |

### Week 16 · HITL 与里程碑

| Day | 主题 | Coding |
|-----|------|--------|
| D76 | 人机确认节点 | approve/reject |
| D77 | 冲突与循环检测 | 防护 |
| D78 | 成本：多智能体放大效应 | 预算限制 |
| D79 | 可演示脚本与样例任务 | demo script |
| D80 | 里程碑：`research-crew` 验收 | 项目打磨 |

---

## 里程碑验收清单

- [ ] 至少 2 个专职 Agent（如 Researcher、Writer）
- [ ] 有共享上下文或消息传递
- [ ] 输出包含过程痕迹（谁做了什么）
- [ ] 支持一处 HITL（例如发布前确认）
- [ ] 有步数/费用上限
- [ ] README 画清协作拓扑

---

## 完成后进入

→ [Phase 5：工程化](./phase-05-engineering.md)
