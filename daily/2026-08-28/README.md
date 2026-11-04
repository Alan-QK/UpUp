# Day 27｜校验失败重试

> 日期：2026-08-28（周五）  
> Phase 2 / Week 6 · 学习日序号：**D27 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清 **repair loop**：校验失败 → 把错误摘要喂回模型 → 再生成，直到成功或用尽次数
2. 区分「抽不出 JSON / JSON 语法坏 / Schema 校验失败」三类错误，并给模型不同提示重点
3. 实现 **最多 3 次修复重试**（首次失败后再修，合计最多 1+3 次模型调用）
4. 用可注入的 mock LLM 把整条回路测绿（不接真实 API）

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 6 · D27）
2. 今日笔记：[`notes.md`](./notes.md)
3. 昨日地基：[`../2026-08-27/notes.md`](../2026-08-27/notes.md)（pydantic 校验与错误摘要）

重点抓住三件事：

- **错误是 Prompt 的一部分**：人类改代码靠 traceback；模型改 JSON 靠可读的字段路径 + 原因
- **次数有硬顶**：无限重试 = 烧钱 + 死循环；今日默认 `max_repairs=3`
- **消息要追加，别覆盖**：assistant 坏输出 + user 修复指令都要进对话历史

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

沿用 Day 26：

```bash
python3 -m pip install --user 'pydantic>=2'
```

### 任务

1. 完成 `exercise/repair_loop.py` 中标有 TODO 的函数（Schema / 抽取 / 校验**已给出**，勿改）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-08-28/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --demo --fail-twice
python3 main.py --demo --always-bad
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `build_repair_user_message` 含错误摘要，并要求「只输出修复后的 JSON」
- [ ] `run_repair_loop`：首次失败后最多再修复 `max_repairs` 次（默认 3）
- [ ] 成功/耗尽都能返回带 `attempts` 轨迹的 `RepairResult`
- [ ] 不要引入 langchain / openai（用可注入的 `llm` 可调用对象）

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能画出：generate → parse → fail? → repair message → 再 generate 的流程图
- [ ] 我知道为什么要把**失败的 assistant 原文**也追加进 messages
- [ ] 我能解释：`max_repairs=3` 与「最多调用模型几次」的关系
- [ ] 我清楚：repair 解决的是格式/契约问题，解决不了「事实瞎编」（那是 RAG / 工具的事）

---

## 本周地图（Week 6）

| Day | 主题 |
|-----|------|
| 26 | JSON + pydantic 校验 |
| **27** | **校验失败重试（repair loop）** ← 今天 |
| 28 | 函数 → JSON Schema（工具预备） |
| 29 | 批量信息抽取 |
| 30 | 周挑战：会议纪要结构化 |
