# Day 4｜模块化与 pytest 入门

> 日期：2026-07-23（周四）  
> Phase 1 / Week 1 · 学习日序号：**D4 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 用「模块 / 包」拆分代码，而不是把一切塞进一个 `.py`
2. 理解 `import`、`__init__.py`、公共 API 的基本约定
3. 用 `pytest` 为工具函数补至少 **3** 个单元测试
4. 建立习惯：Agent 工具函数先有测试，再接 LLM（否则调试成本会爆炸）

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 1 部分）
2. 今日笔记：[`notes.md`](./notes.md)

重点抓住三件事：

- **模块 = 可复用边界**：前端里的「utils 文件 / 共享包」
- **测试是说明书**：`assert` 写清「输入 → 输出 / 异常」
- **先测纯函数**：截断文本、规范化空白、抽标签块——这些不依赖网络，最适合练 pytest

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 任务

`prompt_utils.py` **已经实现好了**。你今天的工作是：**补测试**。

1. 阅读 `exercise/prompt_utils.py`（三个工具函数）
2. 打开 `exercise/tests/test_prompt_utils.py`，完成 TODO（至少 **3** 个有意义的用例）
3. 运行：

```bash
cd daily/2026-07-23/exercise
pip install pytest   # 或 uv pip install pytest
python -m pytest -q
```

4. 可选手工确认：

```bash
python main.py
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] 至少 3 个你自己写的测试函数（不要只留示例）
- [ ] 覆盖「正常路径」和至少 1 个「异常 / 边界」路径
- [ ] 你能用一句话说明：为什么 Agent 工具函数要优先单测

---

## 参考实现

先自己写测试。卡住超过 15 分钟再看：[`solution/tests/test_prompt_utils.py`](./solution/tests/test_prompt_utils.py)

---

## 自检清单

- [ ] 我知道模块与包的差别（有没有 `__init__.py` 目录）
- [ ] 我能写出 `assert` 与 `pytest.raises` 基本写法
- [ ] 我知道 `python -m pytest` 如何发现 `tests/test_*.py`
- [ ] 我已知下一步是 Day 5：周挑战 · 迷你 CLI 工具

---

## 通知摘要（便于推送）

**Day 4｜模块化与 pytest 入门**  
阅读 prompt 工具模块，为 `normalize_whitespace` / `truncate` / `extract_tagged_block` 补至少 3 个单元测试。  
路径：`daily/2026-07-23/`
