# Day 21 练习说明

```bash
python3 -m pytest -q
python3 main.py --demo
python3 main.py --demo --task "把这段话改写成三条要点"
```

今日重点：

1. `prompt_builder.py` — **请你实现** `PromptSpec`、校验、章节渲染与 `build_chat_messages`
2. `main.py` — Demo 入口已给齐：打印 system / user 消息
3. 依赖：仅标准库 + `pytest`（无需 httpx / openai SDK）
