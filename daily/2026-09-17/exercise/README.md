# Day 41 练习说明

```bash
python3 -m pytest -q
python3 main.py --demo
python3 main.py --classify --tools --side-effects
python3 main.py --table
```

今日重点：

1. `agent_vs_chatbot.py` — **请你实现** 对照表行、信号分类、场景校验与 Markdown 渲染
2. `main.py` — Demo 入口已给齐：打印对照表 / 分类结果 / 示例报告
3. 依赖：仅标准库 + `pytest`（无需 httpx / openai SDK）
