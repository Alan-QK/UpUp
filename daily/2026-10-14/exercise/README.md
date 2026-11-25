# Day 58 练习说明

```bash
python3 -m pytest -q
python3 main.py --demo
python3 main.py --branch tool_ok
python3 main.py --branch deny
python3 main.py --report
```

今日重点：

1. `mock_llm_agent.py` — **请你实现** MockLLM、Guard 执行、Loop、场景脚本、覆盖报告
2. `main.py` — Demo 入口已给齐
3. 依赖：仅标准库 + `pytest`（无需真实 LLM）
