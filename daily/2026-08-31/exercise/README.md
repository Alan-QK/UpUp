# Exercise · Day 28 从函数到 JSON Schema

## 目标

用纯标准库把 Python 函数转成 OpenAI 风格的 **tool JSON Schema**（不调用真实 LLM）。

## 依赖

```bash
python3 -m pip install --user pytest   # 仅测试需要
```

## 文件

| 文件 | 说明 |
|------|------|
| `tool_schema.py` | 完成 TODO：注解映射 / docstring / parameters / tools[] |
| `main.py` | 已给齐，打印示例 schema |
| `tests/test_tool_schema.py` | 验收测试 |

## 运行

```bash
cd daily/2026-08-31/exercise
python3 -m pytest -q
python3 main.py
```

## 约束

- 只用标准库（`inspect` / `typing` / `re`）
- 不要引入 pydantic / langchain / openai
- `*args` / `**kwargs` 直接拒绝（tool 参数必须可枚举）
