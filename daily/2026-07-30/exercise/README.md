# Day 8 练习说明

```bash
python3 -m pip install --user httpx pytest
python3 -m pytest -q
python3 main.py
```

今日重点：

1. `async_fetcher.py` — **请你实现** `fetch_one` / `fetch_many`
2. `main.py` — Mock 演示已搭好（并发 3 路），一般不用改
3. 测试全部离线（`httpx.MockTransport`），用 `asyncio.run` 驱动协程
4. 不要用同步 `httpx.Client`；不要顺序 `await` 三个请求假装并发
