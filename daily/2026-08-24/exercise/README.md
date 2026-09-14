# Day 23 练习说明

```bash
python3 -m pytest -q
python3 main.py --demo
python3 main.py --demo --case ages
```

今日重点：

1. `cot_lab.py` — **请你实现** Direct / CoT 两套 Prompt、答案抽取与对比报告
2. `main.py` — Demo 入口已给齐：用内置 mock 输出打印对比表
3. 依赖：仅标准库 + `pytest`（无需 httpx / openai SDK）
