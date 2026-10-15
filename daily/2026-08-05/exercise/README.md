# Exercise · Day 12 角色化多轮助手

## 依赖

```bash
python3 -m pip install --user httpx pytest
```

## 你要做的事

1. [`chat_client.py`](./chat_client.py) **已给齐**（Day 11 完成版），不必改
2. 完成 [`persona_assistant.py`](./persona_assistant.py) 里的 TODO：
   - 固定 `system` 人设
   - `ask` 组装「system + 历史 + 本轮 user」并追加历史
   - `reset` / `history`
3. [`main.py`](./main.py) 已给齐：`--demo` 离线多轮试跑

## 验证

```bash
cd daily/2026-08-05/exercise
python3 -m pytest -q
python3 main.py --demo
python3 main.py --demo -m "第一问" -m "第二问还记得吗"
```
