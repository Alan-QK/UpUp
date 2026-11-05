# Day 58｜Mock LLM 单测

> 日期：2026-10-14（周三）  
> Phase 3 / Week 12 · 学习日序号：**D58 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说明为什么 Agent 单测必须 **Mock LLM**（确定性、零密钥、可覆盖分支）
2. 实现一个可脚本化的 `MockLLM`：按序吐消息、记录每次入参
3. 用假模型驱动带 **Guard** 的最小 Agent Loop，覆盖合法调用 / 拒绝 / `max_steps`
4. 写出能稳定断言的 pytest（对 `stopped_reason`、观察文本、调用次数下手）

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 12 · D58）
2. 今日笔记：[`notes.md`](./notes.md)

重点抓住三件事：

- **Mock ≠ 偷懒**：是把「模型行为」变成可注入的测试夹具
- **按分支测**：最终回答、工具成功、Guard deny、触顶 `max_steps`
- **断言观察层**：不要断言「模型想了什么」，断言系统**做了什么**

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain；**不要**调用真实 LLM。

### 任务

1. 完成 `exercise/mock_llm_agent.py` 中的 TODO  
   （MockLLM、脚本消息工厂、带 Guard 的 Loop、覆盖报告）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-10-14/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --branch final
python3 main.py --branch tool_ok
python3 main.py --branch deny
python3 main.py --branch max_steps
python3 main.py --report
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] `MockLLM` 按序返回；耗尽时抛 `RuntimeError`（消息含 `exhausted` 或 `no more`）
- [ ] 直接最终回答 → `stopped_reason == final_answer`
- [ ] 合法 `order_lookup` → 观察含订单摘要，再出最终回答
- [ ] 未知工具 / 坏参数 → 观察含 `denied`（或等价拒绝词），可继续到最终回答
- [ ] 工具调用步数触顶 → `stopped_reason == max_steps`
- [ ] `render_coverage_report` 含规定二级标题
- [ ] 全程标准库

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能讲清：前端测组件用 mock fetch，Agent 测 Loop 用 Mock LLM
- [ ] 我知道该断言 `stopped_reason` / tool 观察，而不是「模型措辞」
- [ ] 我能列出至少 4 条关键分支（终答 / 工具成功 / deny / max_steps）
- [ ] 我已知明天 Day 59：HITL 确认钩子（危险操作需用户确认）

---

## 本周预告（Week 12）

| Day | 主题 |
|-----|------|
| 56 | Prompt Injection 案例集 |
| 57 | 工具白名单与参数校验 |
| **58** | **Mock LLM 单测（今天）** |
| 59 | HITL 确认钩子 |
| 60 | 里程碑：`tool-agent` 验收 |

---

## 通知摘要（便于推送）

**Day 58｜Mock LLM 单测**  
用脚本化假模型驱动带 Guard 的 Agent Loop，用 pytest 覆盖终答 / 工具成功 / 拒绝 / max_steps。  
路径：`daily/2026-10-14/`
