# Day 49｜轨迹日志 Trace

> 日期：2026-09-30（周三）  
> Phase 3 / Week 10 · 学习日序号：**D49 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说明为什么 Agent 需要**结构化 Trace**，而不是只靠 `print(messages)`
2. 把每一步拆成 Thought / Action / Observation，并格式化打印
3. 把整段轨迹写成 **JSONL**，再加载回来做文本回放
4. 在 Loop 中接入 `live_print`，边跑边看每步决策

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 10 · D49）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾昨日错误恢复：[`../2026-09-29/notes.md`](../2026-09-29/notes.md)

重点抓住三件事：

- **结构在前，展示在后**：先记 `TraceStep`，再渲染文本
- **JSONL 可追加、可回放**：一行一步，评测与排障都方便
- **Live Print = 即时 DevTools**：调试开、单测接 `StringIO`

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain / pydantic。

### 任务

1. 完成 `exercise/trace_log.py` 中的 TODO（`tools.py` **已给齐**，勿改接口）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-09-30/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --multi
python3 main.py --jsonl /tmp/day49-trace.jsonl
python3 main.py --replay /tmp/day49-trace.jsonl
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] `format_action_line` / `format_observation_line` / `format_step_block` 输出规范
- [ ] `dump_trace_jsonl` ↔ `load_trace_jsonl` 往返一致
- [ ] `run_traced_loop` 在 `live_print=True` 时逐步打印 Action/Observation
- [ ] `TracePolicy` 校验拒绝 bool / 非法整数
- [ ] 全程标准库；工具箱继续只有 `lookup` + `calculate`

---

## 参考实现

先自己做。卡住超过 25 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能说清：结构化 Trace 与「整段 dump messages」的差别
- [ ] 我知道 JSONL 为什么适合边跑边追加
- [ ] 我能解释 `live_print` 在调试与单测中的不同接法
- [ ] 我已知明天 Day 50：周挑战——只读文件助手

---

## 本周预告（Week 10）

| Day | 主题 |
|-----|------|
| 46 | ReAct 与 Agent Loop |
| 47 | 终止条件与步数限制 |
| 48 | 工具错误恢复 |
| **49** | **轨迹日志 Trace（今天）** |
| 50 | 周挑战：只读文件助手 |

---

## 通知摘要（便于推送）

**Day 49｜轨迹日志 Trace**  
把每步 Thought / Action / Observation 打成可回放记录；支持 live print 与 JSONL 往返。  
路径：`daily/2026-09-30/`
