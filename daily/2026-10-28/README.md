# Day 62｜摘要记忆

> 日期：2026-10-28（周三）  
> Phase 4 / Week 13 · 学习日序号：**D62 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清「窗口裁掉」与「摘要压缩」的差别：旧轮不是消失，而是**压成一段 summary**
2. 实现可插拔的 `summarizer`（今天用确定性 mock，不上真实 LLM）
3. 完成 `SummarizingMemory`：超出 `keep_recent_turns` 时自动折叠旧轮
4. 组装发给模型的上下文：`system` + `[对话摘要]` + 最近若干轮

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-04-memory-multiagent.md`](../../curriculum/phases/phase-04-memory-multiagent.md)（Week 13 · D62）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾：Day 61 增强窗口（`daily/2026-10-27/`）

重点抓住三件事：

- **摘要记忆 = 有损压缩**：省 token，但细节可能丢
- **滚动摘要**：新的旧轮叠进已有 summary，而不是每次从零重写全历史
- **可插拔**：生产用 LLM summarize；练习用 `default_summarize` 保证可测

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain；**不要**调用真实 LLM。

### 任务

1. 完成 `exercise/summary_memory.py` 中的 TODO  
   （token 估算、默认摘要器、折叠压缩、会话封装、Markdown 报告）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-10-28/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --roll
python3 main.py --report
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] `keep_recent_turns` 之外的完整轮会被折叠进 summary
- [ ] 已有 summary 时，新折叠会**追加合并**，不是覆盖成空白
- [ ] `context_messages()` 顺序：system → 摘要消息（若有）→ 最近轮
- [ ] 不修改入参；折叠后最近轮数精确等于 `keep_recent_turns`（若输入足够）
- [ ] `render_summary_report` 含规定二级标题
- [ ] 全程标准库

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能解释：为什么摘要是「有损」，什么时候该 pin 原文而不是只靠摘要
- [ ] 我知道 mock summarizer 与真实 LLM summarizer 的接口应保持一致
- [ ] 我能画出：短窗口（D61）→ 摘要（今天）→ 向量长期记忆（D63）
- [ ] 我已知明天 Day 63：跨会话的长期向量记忆

---

## 本周预告（Week 13 · 记忆系统）

| Day | 主题 |
|-----|------|
| 61 | 会话记忆回顾 / 增强窗口 |
| **62** | **摘要记忆（今天）** |
| 63 | 长期向量记忆 |
| 64 | 记忆写入策略 |
| 65 | 周挑战：带记忆助理 |

---

## 通知摘要（便于推送）

**Day 62｜摘要记忆**  
超长对话自动折叠：旧轮压成滚动摘要，上下文 = system + 摘要 + 最近轮。  
路径：`daily/2026-10-28/`
