# Day 57 练习说明

```bash
python3 -m pytest -q
python3 main.py --demo
python3 main.py --call order_lookup --args '{"order_id":"ORD-1001"}'
python3 main.py --call shell_exec --args '{"cmd":"rm -rf /"}'
python3 main.py --report
```

今日重点：

1. `tool_guard.py` — **请你实现** 允许列表、Schema 校验、授权、受护调用、Markdown 报告
2. `main.py` — Demo 入口已给齐
3. 依赖：仅标准库 + `pytest`（无需真实 LLM）
