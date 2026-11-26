# Day 71｜何时用多智能体

> 日期：2026-11-26（周四）  
> Phase 4 / Week 15 · 学习日序号：**D71 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清：多智能体解决的是**分工与交接**，不是「多叫几个模型更聪明」
2. 用一套适用 / 不适用信号，给真实任务打分并给出推荐
3. 识别三类否决：角色模糊、纯单技能循环、得分非正
4. 输出一份可复习的决策清单（为 Day 72 流水线双 Agent 做准备）

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-04-memory-multiagent.md`](../../curriculum/phases/phase-04-memory-multiagent.md)（Week 15 · D71）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾：Day 70 的「单 Agent 多步闭环」——多智能体是它的升级，不是替代

重点抓住三件事：

- **先问该不该拆，再问怎么拆**
- **协调税真实存在**：延迟、成本、调试复杂度都会上升
- **前端迁移**：多智能体 UI ≈ 多负责人看板，不是一个更大的聊天泡泡

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**调用 LLM。

### 任务

1. 完成 `exercise/multiagent_decision.py` 中的 TODO  
   （信号收集 / 打分 / 否决规则 / 清单渲染 / 演示场景）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-11-26/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --checklist
python3 main.py --report
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] 六条演示覆盖 `use_multi` / `keep_single` / `defer`
- [ ] 角色模糊、单技能循环能被否决为 `keep_single`
- [ ] `render_checklist` 含 Pro / Con / 结论三节
- [ ] `render_decision_report` 含规定二级标题
- [ ] 全程标准库

---

## 参考实现

先自己做。卡住超过 25 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能用一句话解释：什么时候**不该**上多智能体
- [ ] 我能列出至少 3 条适用信号与 3 条不适用信号
- [ ] 我知道 Day 70 的单 Agent 多步闭环，和多智能体的差别
- [ ] 我已知明天 Day 72：流水线 Researcher → Writer

---

## 本周预告（Week 15 · 多智能体入门）

| Day | 主题 |
|-----|------|
| **71** | **何时用多智能体（今天）** |
| 72 | 流水线：Research → Write |
| 73 | 主管-工人模式 |
| 74 | 共享黑板 / 消息总线 |
| 75 | 周挑战：三角色协作 |

---

## 通知摘要（便于推送）

**Day 71｜何时用多智能体**  
用适用/不适用信号给任务打分，输出 `use_multi` / `keep_single` / `defer` 决策清单。  
路径：`daily/2026-11-26/`
