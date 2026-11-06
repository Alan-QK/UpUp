# Day 26｜JSON 结构化输出

> 日期：2026-08-27（周四）  
> Phase 2 / Week 6 · 学习日序号：**D26 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清「模型自由文本」和「可校验 JSON」差在哪，以及为什么 Agent 必须要后者
2. 用 **pydantic v2** 定义输出契约（字段类型、枚举、范围、默认值）
3. 从带废话 / 代码围栏的模型回复里抽出 JSON，再用 `model_validate` 校验
4. 把 `ValidationError` 转成可读的中文错误列表，为明日的 repair loop 做准备

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 6 · D26）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾：Day 25 的 JSON 抽取与手写校验

重点抓住三件事：

- **契约 = Schema**：类型与约束写在代码里，而不是靠 Prompt「口头约定」
- **校验在边界**：模型输出一进程序，立刻 `validate`；别等下游炸
- **错误要可机器读**：字段路径 + 原因，才能喂回模型做修复（Day 27）

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

本练习首次引入第三方库（仅此一个）：

```bash
python3 -m pip install --user 'pydantic>=2'
```

### 任务

1. 完成 `exercise/structured.py` 中的 TODO
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-08-27/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --demo --show-schema
python3 main.py --demo --bad
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `TaskItem` / `TaskBatch` 用 pydantic 定义，含枚举与字段约束
- [ ] 能从围栏/前后废话中抽出 JSON 对象
- [ ] `parse_task_batch` 用 `model_validate`；非法数据抛出带路径的错误摘要
- [ ] `schema_for_prompt` 能把模型 JSON Schema 压成可放进 Prompt 的文本
- [ ] 不要引入 langchain / openai（校验逻辑离线可测）

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能向同事讲清：为什么「手写 if」升级到 pydantic 更适合 Agent 输出
- [ ] 我知道 `model_validate` 与 `model_validate_json` 的差别
- [ ] 我能解释：Schema 既给校验器用，也可以塞进 Prompt 当「格式说明书」
- [ ] 我清楚：校验失败后下一步不是 `print` 了事，而是准备修复重试（Day 27）

---

## 本周地图（Week 6）

| Day | 主题 |
|-----|------|
| **26** | **JSON + pydantic 校验** ← 今天 |
| 27 | 校验失败重试（repair loop） |
| 28 | 函数 → JSON Schema（工具预备） |
| 29 | 批量信息抽取 |
| 30 | 周挑战：会议纪要结构化 |
