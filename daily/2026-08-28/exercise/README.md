# Exercise · Day 27 校验失败重试

## 目标

实现结构化输出的 **repair loop**：校验失败后把错误摘要喂回模型，最多修复重试 3 次。

本练习 **不调用真实 LLM**：通过注入假 `llm` 可调用对象完成闭环测试。

## 依赖

```bash
python3 -m pip install --user 'pydantic>=2'
```

## 文件

| 文件 | 说明 |
|------|------|
| `repair_loop.py` | Schema/抽取/校验已给出；完成 TODO（repair 相关） |
| `main.py` | 已给齐，阅读即可 |
| `tests/test_repair_loop.py` | 验收测试 |

## 运行

```bash
cd daily/2026-08-28/exercise
python3 -m pytest -q
python3 main.py --demo
python3 main.py --demo --fail-twice
python3 main.py --demo --always-bad
```

## 约束

- 使用 pydantic v2
- 不要引入 langchain / openai
- `max_repairs` 默认 3：首次失败后再修，总调用 ≤ `1 + max_repairs`
