# Exercise · Day 65 周挑战：带记忆助理

## 你要完成什么

编辑 `memory_assistant.py`，把本周记忆能力拼成一个**可跨运行**的助理：

1. `FileMemoryStore` — JSON 持久化 + upsert / search / save / load
2. `build_mock_reply` — 无 LLM，把召回偏好拼进回复
3. `MemoryAssistant.handle_turn` — 召回 → 回复 → 写入闸门 → 落盘
4. `run_cross_session_demo` — 两次独立实例，共享同一文件
5. `render_memory_assistant_report` — 含五个规定二级标题

`decide_write` / `mock_embed` / 数据结构**已给齐**，复用即可。

## 怎么跑

```bash
python3 -m pip install --user pytest
cd daily/2026-11-03/exercise
python3 -m pytest -q
python3 main.py --demo
python3 main.py --report
```

## 提示

1. **跨运行 = 文件**，不是把 list 放在全局变量里
2. `MemoryAssistant(path)` 构造时 `FileMemoryStore` 应自动 `load()` 已有文件
3. 会话 2 必须 `MemoryAssistant(...)` **新实例**，不要复用会话 1 对象
4. ASK 默认 `confirm_fn` 返回 False；测试会注入 True 验证 HITL 路径
5. `save` 建议写 `.tmp` 再 `replace`，避免写到一半崩溃留下坏文件
