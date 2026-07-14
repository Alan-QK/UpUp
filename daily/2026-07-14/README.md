# Day 1｜环境搭建与 Python 项目结构

> 日期：2026-07-14（周二）  
> Phase 1 / Week 1 · 学习日序号：**D1 / 120**  
> 建议时长：**70 分钟**（概念 25 + Coding 40 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 在本机用虚拟环境跑起一个最小 Python 项目
2. 理解「项目结构约定」为什么对后续 Agent 工程重要
3. 写出带**类型注解**的函数，并用 `pytest` 跑通第一个测试

---

## 学习内容（25 分钟）

请先阅读：

1. [`curriculum/00-总纲.md`](../../curriculum/00-总纲.md)（若尚未读完）
2. 今日笔记：[`notes.md`](./notes.md)

重点抓住三件事：

- **虚拟环境**：依赖隔离，避免污染全局 Python
- **类型注解**：不是装饰，是给未来 Agent 工具/schema 打地基
- **可测试**：从 Day 1 就用 pytest，后面 Mock LLM 会很省事

---

## Coding 练习（40 分钟）

目录：[`exercise/`](./exercise/)

### 任务

1. （可选但推荐）安装 [`uv`](https://github.com/astral-sh/uv) 或使用 `python -m venv .venv`
2. 在 `exercise/` 下安装 pytest：`pip install pytest`（或 `uv pip install pytest`）
3. 完成 `exercise/greeter.py` 中的 TODO
4. 运行测试：

```bash
cd daily/2026-07-14/exercise
pytest -q
```

5. 运行手工脚本：

```bash
python main.py
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `greet` / `greet_many` 都有完整类型注解
- [ ] 空名字会抛出 `ValueError`
- [ ] 你能用一句话解释：为什么 Agent 项目也需要类型注解

---

## 参考实现

先自己做。卡住超过 15 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能创建/激活虚拟环境
- [ ] 我知道本仓库 `daily/`、`curriculum/`、`projects/` 各自干什么
- [ ] 我写下了今天的 3 条笔记（可写在 notes 末尾「我的记录」）
- [ ] 我已知下一步是 Day 2：dataclass 与异常设计

---

## 通知摘要（便于推送）

**Day 1｜环境搭建与 Python 项目结构**  
完成虚拟环境 + 类型注解练习 `greeter.py`，跑通 pytest。  
路径：`daily/2026-07-14/`
