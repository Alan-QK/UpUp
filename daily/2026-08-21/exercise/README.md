# Day 22 练习说明

```bash
python3 -m pytest -q
python3 main.py --demo
python3 main.py --demo --text "登录按钮点了没反应"
```

今日重点：

1. `few_shot.py` — **请你实现** 示例数据结构、校验、正/反例渲染与 `build_classification_messages`
2. `main.py` — Demo 入口已给齐：打印 system / user messages
3. 依赖：仅标准库 + `pytest`（无需 httpx / openai SDK）
