# Exercise · Day 14 Token 与成本意识

## 依赖

核心练习（`usage_meter.py` + 单测）只需标准库 + pytest：

```bash
python3 -m pip install --user pytest
```

若运行 `main.py --with-chat`（复用 Day 11 ChatClient）：

```bash
python3 -m pip install --user httpx
```

## 你要做的事

1. 完成 [`usage_meter.py`](./usage_meter.py) 里的 TODO
2. [`chat_client.py`](./chat_client.py) 已给齐，不必改
3. [`main.py`](./main.py) 已给齐：`--demo` 打印估算与汇总；加 `--with-chat` 用 Mock 聊天并记账

## 验证

```bash
cd daily/2026-08-07/exercise
python3 -m pytest -q
python3 main.py --demo
python3 main.py --demo --with-chat
```
