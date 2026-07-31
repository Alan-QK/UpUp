# Day 6 练习说明

```bash
python3 -m pip install --user httpx pytest
python3 -m pytest -q
python3 main.py
```

今日重点：

1. `json_client.py` — **请你实现** `JsonClient` / `HttpStatusError` / `HttpResponseError`
2. `main.py` — MockTransport 演示已搭好，一般不用改
3. 测试全部离线（`httpx.MockTransport`），不依赖外网
