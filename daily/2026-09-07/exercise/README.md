# Day 33 练习说明

```bash
python3 -m pip install --user pytest httpx
python3 -m pytest -q
python3 main.py --demo
python3 main.py --demo --batch-size 2
python3 main.py --demo --similar
```

今日重点：

1. `embedder.py` — **请你实现** TODO：HTTP 客户端、响应解析、切批、余弦相似度
2. 异常类 / dataclass **已给出，勿改字段名**
3. `main.py` — 演示已搭好：`--demo` 走 MockTransport，不访问外网
4. 依赖：`httpx` + `pytest`（不要引入 openai / langchain SDK）
