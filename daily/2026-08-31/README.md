# Day 28｜从函数到 JSON Schema

> 日期：2026-08-31（周一）  
> Phase 2 / Week 6 · 学习日序号：**D28 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清 **Tool Calling** 里模型看到的不是 Python 函数，而是一份 **JSON Schema 契约**
2. 用 `inspect.signature` + `typing` 把函数注解映射到 JSON Schema（string/integer/array/enum…）
3. 生成符合 OpenAI Chat Completions `tools[]` 形状的 tool 定义
4. 分清：`required`、默认值、`Optional` / `| None` 三者如何影响「必填」

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 6 · D28）
2. 今日笔记：[`notes.md`](./notes.md)
3. 昨日地基：[`../2026-08-28/notes.md`](../2026-08-28/notes.md)（结构化校验与 repair）

重点抓住三件事：

- **前端类比**：TS 函数类型 / Zod schema → 运行时契约；今天是 Python → JSON Schema
- **给模型看 schema，不给源码**：模型按 `parameters.properties` 填参数
- **这是 Phase 3 的预热**：后面真正执行 tool call 时，schema 就是路由表

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

纯标准库，无需额外安装（测试仍用 pytest）：

```bash
python3 -m pip install --user pytest   # 若尚未安装
```

### 任务

1. 完成 `exercise/tool_schema.py` 中标有 TODO 的函数
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-08-31/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `annotation_to_json_schema` 覆盖 str/int/float/bool、list[T]、dict、Literal、Optional
- [ ] `function_to_parameters_schema` 的 `required` 规则与测试一致
- [ ] `function_to_tool_schema` 输出 `{type:function, function:{name,description,parameters}}`
- [ ] 不要引入 pydantic / langchain / openai（今日刻意用手写映射）

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能徒手写出一个 `get_weather(city, unit?)` 对应的 tool JSON（不必完美，结构要对）
- [ ] 我知道为什么 `unit: str = "celsius"` 不进 `required`，而 `city: str` 会进
- [ ] 我知道 `tag: str | None = None` 的 schema type 仍是 string，但 tag 不在 required
- [ ] 我能解释：今天的 schema 生成，和 Day 26 pydantic 校验分别服务「告诉模型」与「验收模型」

---

## 本周地图（Week 6）

| Day | 主题 |
|-----|------|
| 26 | JSON + pydantic 校验 |
| 27 | 校验失败重试（repair loop） |
| **28** | **函数 → JSON Schema（工具预备）** ← 今天 |
| 29 | 批量信息抽取 |
| 30 | 周挑战：会议纪要结构化 |
