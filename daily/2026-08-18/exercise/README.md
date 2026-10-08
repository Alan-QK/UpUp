# Day 20 练习说明

```bash
python3 -m pip install --user httpx   # 若尚未安装
python3 -m pytest -q
python3 main.py --demo --line "你好" --line /history --line /reset --line "新话题" --line /exit
```

今日重点：

1. `streaming_assistant.py` — **请你实现** `StreamingWindowedAssistant`
2. `streaming_client.py` / `history_window.py` / `env_loader.py` / `chat_session.py` / `main.py` **已给齐**
3. 测试全部 Mock SSE，不访问外网
4. 完成后对照 `../solution/`，并把打磨版放到 `projects/cli-chatbot/`
