# Exercise · Day 26 JSON 结构化输出

## 目标

用 **pydantic v2** 定义任务清单的输出契约，并从「脏」的模型回复中抽出、校验 JSON。

本练习 **不调用真实 LLM**：抽取 + 校验离线可测；`main.py` 用 mock 回复演示。

## 依赖

```bash
python3 -m pip install --user 'pydantic>=2'
```

## 文件

| 文件 | 说明 |
|------|------|
| `structured.py` | 完成全部 TODO |
| `main.py` | 已给齐，阅读即可 |
| `tests/test_structured.py` | 验收测试 |

## 运行

```bash
cd daily/2026-08-27/exercise
python3 -m pytest -q
python3 main.py --demo
python3 main.py --demo --show-schema
python3 main.py --demo --bad
```

## 约束

- 使用 pydantic v2（`BaseModel` / `Field` / `ValidationError`）
- 不要引入 langchain / openai
- JSON 抽取可用标准库；不要用贪婪正则 `\{.*\}` 硬切
