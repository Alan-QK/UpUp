# Day 52｜框架重写手写 Agent

> 日期：2026-10-05（周一）  
> Phase 3 / Week 11 · 学习日序号：**D52 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 把 Day 46 手写 Loop 的概念，映射到框架常见抽象（Tool / Agent / Runner / State）
2. 用一份**教学用迷你框架 API** 重写同能力 Agent（lookup + calculate），行为与手写版对齐
3. 说出「框架内部仍是 Loop」——只是把样板代码收进了类与注册表
4. 产出一张 **手写 ↔ 框架** 对照表（方便明天接真实框架工具）

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 11 · D52）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾手写 Loop：[`../2026-09-25/notes.md`](../2026-09-25/notes.md)
4. 回顾选型：[`../2026-10-02/notes.md`](../2026-10-02/notes.md)

重点抓住三件事：

- **同能力对照**：同一目标、同一工具、同一 `ScriptedChat`，换一层 API 外壳
- **抽象落点**：`@tool` / Registry ≈ 工具白名单；`Runner.run` ≈ `while` Loop
- **今天不装真框架**：先理解映射，明天再谈真实 SDK 的自定义工具接入

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 langchain / langgraph / openai / llamaindex。

### 任务

1. 完成 `exercise/mini_framework.py` 中的 TODO
2. `tools_builtin.py` 与 `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-10-05/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --goal "查 alpha 再乘以 3"
python3 main.py --mapping
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `Tool` + `ToolRegistry`：注册、列 schema、按名执行（未知工具 → ERROR）
- [ ] `FrameworkAgent` + `AgentRunner.run`：多步 Action → Final，行为对齐 Day46
- [ ] `max_steps` 耗尽时 `stopped_reason=max_steps`
- [ ] `concept_mapping` / `render_mapping_markdown` 能产出手写↔框架对照表
- [ ] 全程标准库（迷你框架是教学外壳，不是真装依赖）

---

## 参考实现

先自己做。卡住超过 15 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能指着手写 `run_agent_loop` 说出对应的 Runner 在哪一层
- [ ] 我知道 ToolRegistry 本质上就是「白名单 + handler 字典」
- [ ] 我能解释：为什么今天用迷你框架，而不是直接 `pip install` 真框架
- [ ] 我已知明天 Day 53：在框架风格 API 上新增 1 个业务工具
