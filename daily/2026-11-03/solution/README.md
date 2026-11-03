# Solution · Day 65

参考实现：`memory_assistant.py`

验证（与 exercise/tests 对齐）：

```bash
TMP=$(mktemp -d)
cp daily/2026-11-03/solution/memory_assistant.py "$TMP/"
cp -r daily/2026-11-03/exercise/tests "$TMP/"
cp daily/2026-11-03/exercise/__init__.py "$TMP/" 2>/dev/null || true
cd "$TMP" && python3 -m pytest -q
```

要点：

- `FileMemoryStore.save` 使用临时文件再 `replace`
- `MemoryAssistant` 每轮：search → reply → decide_write → 条件 upsert
- `run_cross_session_demo` 用两个实例证明跨运行召回
