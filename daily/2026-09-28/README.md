# Day 47｜终止条件与步数限制

> 日期：2026-09-28（周一）  
> Phase 3 / Week 10 · 学习日序号：**D47 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说出 Agent Loop 至少 **3 种**合理终止原因（最终回答 / 步数触顶 / 重复动作）
2. 设计可配置的 `StopPolicy`：`max_steps` + 连续同指纹工具调用熔断
3. 在「最后一步仍要调工具」时选择 **拦截不执行**，避免白烧一轮工具费用
4. 把「何时停」从硬编码 `if` 升级成**可测的策略对象**

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 10 · D47）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾昨日 Loop：[`../2026-09-25/notes.md`](../2026-09-25/notes.md)

重点抓住三件事：

- **停得住才是生产可用**：没有终止条件的 Loop = 无限费用账单
- **重复 Action 是死循环的最常见形态**：同一工具 + 同一参数连打 N 次 → 熔断
- **最后一步预算**：步数将尽时，宁可强制收尾，也不再执行工具

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain / pydantic。

### 任务

1. 完成 `exercise/stop_guard.py` 中的 TODO（`tools.py` **已给齐**，勿改接口）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-09-28/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --repeat
python3 main.py --last-step
python3 main.py --max-steps
python3 main.py --trace
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] `StopPolicy` 校验拒绝 bool / 非法整数
- [ ] 连续相同工具指纹达到阈值 → `stopped_reason == "repeated_action"`
- [ ] 最后一步仍要工具且 `block_tools_on_last_step=True` → 不执行工具并停止
- [ ] 正常无工具回答仍走 `final_answer`
- [ ] 全程标准库；工具箱继续只有 `lookup` + `calculate`

---

## 参考实现

先自己做。卡住超过 25 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能列出至少 3 种 `stopped_reason` 及其业务含义
- [ ] 我知道「指纹」为什么要用 name + 规范化参数，而不只用 tool name
- [ ] 我能解释：为什么最后一步拦截工具比「执行完再停」更省钱
- [ ] 我已知明天 Day 48：工具错误恢复（非法参数让模型纠正）

---

## 本周预告（Week 10）

| Day | 主题 |
|-----|------|
| 46 | ReAct 与 Agent Loop |
| **47** | **终止条件与步数限制（今天）** |
| 48 | 工具错误恢复 |
| 49 | 轨迹日志 Trace |
| 50 | 周挑战：只读文件助手 |

---

## 通知摘要（便于推送）

**Day 47｜终止条件与步数限制**  
给 Agent Loop 加上可配置停止策略：max_steps、重复动作熔断、最后一步拦截工具。  
路径：`daily/2026-09-28/`
