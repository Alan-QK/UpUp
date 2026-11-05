# Day 57 参考实现

先完成 `../exercise/` 再对照本目录的 `tool_guard.py`。

验证方式（推荐复制到临时目录与测试一起跑）：

```bash
TMP=$(mktemp -d)
cp daily/2026-10-12/solution/tool_guard.py "$TMP/"
cp -r daily/2026-10-12/exercise/tests "$TMP/"
cp daily/2026-10-12/exercise/main.py "$TMP/"
cd "$TMP" && python3 -m pytest -q
```
