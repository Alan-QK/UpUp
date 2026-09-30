# Exercise · Day 16 历史消息裁剪（滑动窗口）

## 依赖

```bash
python3 -m pip install --user httpx pytest
```

## 你要做的事

1. [`chat_client.py`](./chat_client.py) **已给齐**（Day 11 完成版），不必改
2. 完成 [`history_window.py`](./history_window.py) 里的 TODO：
   - `count_turns` / `sliding_window`
   - `WindowedAssistant`（人设常驻 + 请求与本地历史都按 `max_turns` 裁剪）
3. [`main.py`](./main.py) 已给齐：`--demo` 离线观察「旧轮被裁掉」

## 验证

```bash
cd daily/2026-08-11/exercise
python3 -m pytest -q
python3 main.py --demo --max-turns 2
python3 main.py --demo --max-turns 1 -m "A" -m "B" -m "C"
```

对比 `--max-turns 1` 与 `2`：第三轮回复里「记得」的内容应不同。
