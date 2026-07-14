# Phase 3｜Agent 核心：Tool Calling 与 Agent Loop

> 周期：Week 9–12（约 20 个工作日）  
> 关键词：Tools、ReAct、Agent Loop、框架对比、安全边界

---

## 阶段目标

1. 理解 Tool Calling 的协议与设计原则
2. **手写**一个最小 Agent Loop（不先依赖重框架）
3. 再引入 1 个主流框架加深理解
4. 交付里程碑：`projects/tool-agent`

---

## 周计划

### Week 9 · Tool Calling 基础

| Day | 主题 | Coding |
|-----|------|--------|
| D41 | 什么是 Agent（相对 Chatbot） | 概念对照笔记 |
| D42 | function/tool schema | 定义 2–3 个工具 |
| D43 | 单轮 tool call 执行 | 执行器 |
| D44 | 多轮 tool 结果回填 | 对话拼接 |
| D45 | 周挑战：计算器 + 时间工具 Agent | 可运行 Demo |

### Week 10 · 手写 Agent Loop

| Day | 主题 | Coding |
|-----|------|--------|
| D46 | ReAct 思想：Reason + Act | 伪代码落地 |
| D47 | 终止条件与最大步数 | 防死循环 |
| D48 | 错误工具调用的恢复 | 友好错误回传 |
| D49 | 日志：每步 thought/action/obs | trace 打印 |
| D50 | 周挑战：文件助手（只读目录） | 权限最小化 |

### Week 11 · 框架对照学习

| Day | 主题 | Coding |
|-----|------|--------|
| D51 | 框架选型原则（少而精） | 选型笔记 |
| D52 | 用框架重写 Week10 Agent | 对照实现 |
| D53 | 内置工具与自定义工具 | 扩展 1 工具 |
| D54 | 流式 + 工具状态事件 | 事件模型 |
| D55 | 周挑战：框架版 vs 手写版对比报告 | 对比文档 |

### Week 12 · 安全与里程碑

| Day | 主题 | Coding |
|-----|------|--------|
| D56 | Prompt Injection 案例 | 攻击样例集 |
| D57 | 工具白名单与参数校验 | 防护层 |
| D58 | 单元测试 Agent（mock LLM） | pytest |
| D59 | 用户确认（HITL）雏形 | confirm 钩子 |
| D60 | 里程碑：`tool-agent` 验收 | 项目打磨 |

---

## 里程碑验收清单

- [ ] 至少 3 个真实工具（如：时间、计算器、HTTP GET、本地文件只读）
- [ ] 手写 Agent Loop 可独立运行
- [ ] 有最大步数与超时
- [ ] 有 trace 日志（每步可回放）
- [ ] 有基础安全约束（禁止任意 shell 等）
- [ ] mock 测试覆盖关键路径

---

## 学习策略提醒

**先手写，再框架。** 否则你会「会调库、不懂 Agent」。

## 完成后进入

→ [Phase 4：记忆 · 规划 · 多智能体](./phase-04-memory-multiagent.md)
