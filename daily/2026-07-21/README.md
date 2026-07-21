# Day 2｜函数、dataclass 与异常设计

> 日期：2026-07-21（周二）  
> Phase 1 / Week 1 · 学习日序号：**D2 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 用 `dataclass` 表达结构化数据（配置、用户、消息……）
2. 用 `Enum` 约束有限取值，避免魔法字符串
3. 设计可读的自定义异常，而不是到处 `raise Exception("随便写")`
4. 写出带清晰输入校验的小模块函数

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 1 部分）
2. 今日笔记：[`notes.md`](./notes.md)

重点抓住三件事：

- **dataclass ≈ 带默认行为的结构化对象**：前端里的「类型清晰的 plain object」
- **异常要分层**：校验失败 ≠ 系统故障；Agent 里要能区分「用户输入坏了」和「模型/工具挂了」
- **函数签名即契约**：参数、返回值、抛什么错，写清楚

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 任务

实现一个迷你「Agent 运行配置 + 用户」模块：

1. 完成 `exercise/models.py` 中的 TODO
2. 完成 `exercise/validate.py` 中的 TODO
3. 运行测试：

```bash
cd daily/2026-07-21/exercise
pip install pytest   # 或 uv pip install pytest
pytest -q
```

4. 运行手工脚本：

```bash
python main.py
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `User` / `AgentConfig` 使用 `@dataclass`
- [ ] `Role` 使用 `Enum`
- [ ] 非法 temperature / 空 name 等会抛出自定义异常（不是裸 `Exception`）
- [ ] 你能用一句话说明：为什么 Agent 配置适合用 dataclass

---

## 参考实现

先自己做。卡住超过 15 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能写出一个带默认值的 `@dataclass`
- [ ] 我知道 `Enum` 和普通字符串常量的差别
- [ ] 我能解释 `ValidationError` 与 `ConfigError` 的使用场景
- [ ] 我已知下一步是 Day 3：文件 I/O、JSON 与 pathlib

---

## 通知摘要（便于推送）

**Day 2｜函数、dataclass 与异常设计**  
实现 `User` / `AgentConfig` dataclass + 自定义校验异常，跑通 pytest。  
路径：`daily/2026-07-21/`
