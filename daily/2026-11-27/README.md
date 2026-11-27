# Day 72｜流水线双 Agent：Research → Write

> 日期：2026-11-27（周五）  
> Phase 4 / Week 15 · 学习日序号：**D72 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清流水线多智能体的本质：**串行交接 + 专职角色**，不是两个模型闲聊
2. 实现最小双 Agent：`Researcher` 产出 `ResearchBrief`，`Writer` 消费它写出 `Article`
3. 用可回放的 `trace` 证明「谁做了什么、交了什么」
4. 理解空交接必须失败——流水线靠契约，不靠默契

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-04-memory-multiagent.md`](../../curriculum/phases/phase-04-memory-multiagent.md)（Week 15 · D72）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾 Day 71：今天只实现「适用」场景里最简单的一种——流水线交接

重点抓住三件事：

- **交接物要结构化**：Brief / Article 是合约，不是一段自由文本糊过去
- **角色工具不同**：Researcher 检索语料；Writer 只读 Brief，不回头搜库
- **前端迁移**：流水线 ≈ 多步表单 / 看板列；每列有明确输入输出

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**调用 LLM（检索与写作都用确定性启发式）。

### 任务

1. 完成 `exercise/pipeline_agents.py` 中的 TODO  
   （检索 / Researcher / Writer / 管线编排 / 报告）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-11-27/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --topic "向量数据库选型"
python3 main.py --report
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] Researcher 只产出 `ResearchBrief`；Writer 只消费 Brief 写 `Article`
- [ ] 空主题 / 空 Brief / 无命中语料会清晰失败
- [ ] `trace` 顺序为 research → write，含交接摘要
- [ ] 报告含规定二级标题
- [ ] 全程标准库

---

## 参考实现

先自己做。卡住超过 25 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能画出 Researcher → Writer 的数据流（含交接物类型）
- [ ] 我知道为什么 Writer **不该**直接访问语料库（角色边界）
- [ ] 我能解释：trace 对调试多智能体为什么比「最终答案」更重要
- [ ] 我已知下周 Day 73：主管-工人模式（路由分派）

---

## 本周预告（Week 15 · 多智能体入门）

| Day | 主题 |
|-----|------|
| 71 | 何时用多智能体 |
| **72** | **流水线：Research → Write（今天）** |
| 73 | 主管-工人模式 |
| 74 | 共享黑板 / 消息总线 |
| 75 | 周挑战：三角色协作 |

---

## 通知摘要（便于推送）

**Day 72｜流水线双 Agent：Research → Write**  
实现 Researcher→Writer 串行交接：结构化 Brief 交给 Writer 成稿，并用 trace 回放协作过程。  
路径：`daily/2026-11-27/`
