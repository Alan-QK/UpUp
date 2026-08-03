# Day 10 练习说明

```bash
python3 -m pip install --user httpx   # 若尚未安装
python3 -m pytest -q
python3 main.py brief Shanghai --demo
```

今日重点：

1. `aggregator.py` — **请你实现** `_get_json` / `fetch_weather` / `fetch_joke` / `build_daily_brief` / `format_brief`
2. `demo_transport()` 已给齐：离线 Mock 天气 + 笑话
3. `main.py` — CLI 已搭好；`--demo` 时注入 Mock，不访问外网
4. 测试全部用 MockTransport；可选验证 `WEATHER_API_KEY` → `Authorization` Header
