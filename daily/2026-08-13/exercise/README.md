# Day 18 练习说明

```bash
python3 -m pytest -q
python3 main.py --demo
```

今日重点：

1. `providers.py` — **请你实现** `FakeChatProvider` 与 `create_chat_provider`（类型与 Protocol 已写好）
2. `openai_compat.py` — OpenAI 兼容实现**已给齐**，对照阅读即可
3. `main.py` — 演示入口已搭好：`--demo` 走 fake；真调走 `openai` + 环境变量
4. 依赖：`httpx`（仅 openai 路径需要）、`pytest`
