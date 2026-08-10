# Day 15 练习说明

```bash
python3 -m pip install --user httpx   # 若尚未安装
python3 -m pytest -q
python3 main.py --demo --line "你好" --line /history --line /reset --line "新话题" --line /exit
```

今日重点：

1. `chat_session.py` — **请你实现** `ChatSession.handle_line` / 斜杠命令 / 历史格式化
2. `chat_client.py`、`persona_assistant.py` **已给齐**（Day 11 / Day 12 完成版）
3. `main.py` — REPL / `--line` 非交互入口已搭好；`--demo` 不访问外网
4. 测试全部用 MockTransport；重点验命令、多轮上下文、错误不崩
