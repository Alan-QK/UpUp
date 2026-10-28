# Exercise · Day 61 增强历史窗口

## 你要完成什么

编辑 `memory_window.py`，实现短时会话记忆的增强裁剪：

- `estimate_tokens` / `message_tokens`
- `count_exchange_turns`
- `apply_enhanced_window`（轮数 + 预算 + pinned/system）
- `SessionMemory`
- `render_window_report`

`build_demo_transcript` 与数据结构已给齐。

## 怎么跑

```bash
python3 -m pip install --user pytest
cd daily/2026-10-27/exercise
python3 -m pytest -q
python3 main.py --demo
python3 main.py --budget
python3 main.py --report
```

## 提示

1. 先写 `estimate_tokens` 与找「完整轮」的小函数，再写窗口
2. 保护项（system / pinned）与可裁剪轮分开处理
3. 有 `max_tokens` 时从**最新轮**往旧装，整轮加减
4. 不要修改入参 list；`history()` 返回副本
