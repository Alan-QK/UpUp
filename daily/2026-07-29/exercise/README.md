# Day 7 练习说明

```bash
python3 -m pip install --user httpx pytest
python3 -m pytest -q
python3 main.py
```

今日重点：

1. `retry_client.py` — **请你实现** 错误分类函数 + `RetryingJsonClient`
2. `main.py` — Mock 演示已搭好（先 503 再成功），一般不用改
3. 测试全部离线（`httpx.MockTransport`），不依赖外网
4. 测试里 `backoff_seconds` 很小（如 `0.01`），避免真的睡很久
