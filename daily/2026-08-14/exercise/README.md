# Day 19 练习说明

```bash
python3 -m pytest -q
python3 main.py --demo
python3 main.py --demo --fail
```

今日重点：

1. `chat_logger.py` — **请你实现** `mask_value`、`should_mask_key`、`StructuredLogger`
2. `main.py` — Demo 入口已给齐：成功一轮 / 故意失败一轮，观察 JSON 日志
3. 依赖：仅标准库 + `pytest`（无需 httpx）
