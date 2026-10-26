# Day 43 练习说明

```bash
python3 -m pytest -q
python3 main.py --demo
python3 main.py --json
python3 main.py --fail
```

今日重点：

1. `tool_executor.py` — **请你实现** 解析 `tool_calls`、注册表路由、执行与 `role=tool` 回填
2. `main.py` — Demo 入口已给齐：成功路径 / JSON 输出 / 故意失败路径
3. 依赖：仅标准库 + `pytest`（无需 httpx / openai / pydantic）

与 Day 42 的衔接：昨天定义契约；今天兑现调用。不要在练习里发真实 LLM 请求。
