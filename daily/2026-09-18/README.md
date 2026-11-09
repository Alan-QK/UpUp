# Day 42｜Tool Schema 设计

> 日期：2026-09-18（周五）  
> Phase 3 / Week 9 · 学习日序号：**D42 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清 Tool Schema 是 Agent 给模型看的 **API 契约**（不是 Python 源码）
2. 按命名 / 描述 / 参数三条原则，**手写** 3 个高质量工具定义
3. 校验 OpenAI 风格 `tools[]` 结构：`type`、`function.name/description/parameters`、`required ⊆ properties`
4. 区分 Day 28「函数反射生成」与今天「产品化设计」：结构对 vs 用得对

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 9 · D42）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾：Day 28 反射生成 [`../2026-08-31/notes.md`](../2026-08-31/notes.md)；昨日边界 [`../2026-09-17/notes.md`](../2026-09-17/notes.md)

重点抓住三件事：

- **契约给模型看**：`name` + `description` + `parameters` 决定会不会乱调工具
- **一工具一事**：天气 / 计算 / 时间三个只读工具，职责清晰
- **设计可编码**：命名、描述长度、required 规则都能写成校验函数

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain / pydantic。

### 任务

1. 完成 `exercise/tool_design.py` 中的 TODO
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-09-18/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --json
python3 main.py --validate
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `build_get_weather_tool` / `build_calculate_tool` / `build_get_current_time_tool` 各自返回合法 tool dict
- [ ] `default_toolkit()` 恰好 3 个工具，名称集合正确且无重复
- [ ] `validate_tool_schema` 能拦住坏名字、坏 required、缺 description
- [ ] `check_design_quality` 能拦住过短描述、空 properties 等设计问题
- [ ] 全程标准库（不要引入 langchain / openai SDK）

---

## 参考实现

先自己做。卡住超过 15 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能徒手写出 `get_weather` 的完整 tool JSON（结构正确即可）
- [ ] 我知道 description 应写「何时调用」，而不只是「这是什么」
- [ ] 我能解释为何 `unit` / `timezone` 不进 `required`
- [ ] 我已知明天 Day 43：解析并执行单轮 `tool_calls`

---

## 本周地图（Week 9）

| Day | 主题 |
|-----|------|
| 41 | Chatbot vs Agent |
| **42** | **Tool Schema 设计** ← 今天 |
| 43 | 单轮 Tool Call 执行 |
| 44 | 工具结果回填多轮 |
| 45 | 周挑战：双工具 Agent |
