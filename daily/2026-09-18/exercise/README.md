# Day 42 练习说明

```bash
python3 -m pytest -q
python3 main.py --demo
python3 main.py --json
python3 main.py --validate
```

今日重点：

1. `tool_design.py` — **请你实现** 命名/结构校验、三个工具 builder、工具箱组装与设计质量检查
2. `main.py` — Demo 入口已给齐：打印 Markdown 摘要 / JSON / 校验结果
3. 依赖：仅标准库 + `pytest`（无需 httpx / openai / pydantic）

与 Day 28 的差异：今天**不**做 `inspect` 反射；你直接设计 dict 契约。
