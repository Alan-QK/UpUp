# Exercise · Day 11 Chat Completions

## 依赖

```bash
python3 -m pip install --user httpx pytest
```

## 你要做的事

完成 [`chat_client.py`](./chat_client.py) 里的 TODO：

- 构造 `httpx.Client`（带 Bearer Header，可注入 `transport`）
- 实现 `complete`：`POST /chat/completions`，`stream=false`
- 解析 `choices[0].message.content` 与可选 `usage`

[`main.py`](./main.py) 已给齐：`--demo` 离线；有 `OPENAI_*` 环境变量时可真调。

## 验证

```bash
cd daily/2026-08-04/exercise
python3 -m pytest -q
python3 main.py --demo
```
