# Day 48｜工具错误恢复

> 日期：2026-09-29（周二）  
> Phase 3 / Week 10 · 学习日序号：**D48 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 解释为什么工具失败**绝不能抛穿 Loop**，而要变成可回填的观察
2. 识别 `ERROR:` 前缀观察，并设计「模型纠正参数再试」的恢复路径
3. 配置 `RecoveryPolicy`：`max_steps` + `max_consecutive_errors`
4. 统计 `recovery_count`，区分「恢复成功」与「连续失败熔断」

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 10 · D48）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾昨日停止策略：[`../2026-09-28/notes.md`](../2026-09-28/notes.md)

重点抓住三件事：

- **失败是 Observation，不是 Crash**：前端表单校验失败会提示用户改，不会整页白屏
- **协议层已有答案**：`role=tool` + `ERROR: ...` 回填 → 下一轮模型自然能改
- **恢复也要有上限**：连续错 N 次仍不改 → `too_many_errors`，别无限烧钱

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain / pydantic。

### 任务

1. 完成 `exercise/error_recovery.py` 中的 TODO（`tools.py` **已给齐**，勿改接口）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-09-29/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --lookup
python3 main.py --fail
python3 main.py --json
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] 缺参 / 未知键 / 坏 JSON 都能以 `ERROR:` 回填并继续 Loop
- [ ] 模型纠正后 `recovery_count >= 1`，最终 `final_answer`
- [ ] 连续 ERROR 步触顶 → `too_many_errors`
- [ ] `RecoveryPolicy` 校验拒绝 bool / 非法整数
- [ ] 全程标准库；工具箱继续只有 `lookup` + `calculate`

---

## 参考实现

先自己做。卡住超过 25 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能说清：工具异常为什么要转成观察，而不是 `raise` 打断 Loop
- [ ] 我知道 `error_action` 与 `action` 的区别，以及何时 `recovery_count += 1`
- [ ] 我能解释 `too_many_errors` 与 Day 47 `repeated_action` 的不同（错误 vs 重复成功动作）
- [ ] 我已知明天 Day 49：轨迹日志 Trace（每步 action/observation 可回放）

---

## 本周预告（Week 10）

| Day | 主题 |
|-----|------|
| 46 | ReAct 与 Agent Loop |
| 47 | 终止条件与步数限制 |
| **48** | **工具错误恢复（今天）** |
| 49 | 轨迹日志 Trace |
| 50 | 周挑战：只读文件助手 |

---

## 通知摘要（便于推送）

**Day 48｜工具错误恢复**  
非法参数 / 未知工具时把 `ERROR:` 观察回填，让模型纠正；连续失败则熔断。  
路径：`daily/2026-09-29/`
