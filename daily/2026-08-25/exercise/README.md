# Day 24 练习说明

```bash
python3 -m pytest -q
python3 main.py --demo
python3 main.py --demo --case role_hijack
```

今日重点：

1. `injection_guard.py` — **请你实现** 注入信号检测、输入包裹、守卫 Prompt、防御评测
2. `main.py` — Demo 入口已给齐：用 3 条恶意样例跑一遍攻防报告
3. 依赖：仅标准库 + `pytest`（无需 httpx / openai SDK）
