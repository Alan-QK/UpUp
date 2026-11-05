# Day 59 参考实现

先自己完成 `../exercise/`，再对照本目录的 `hitl_confirm.py`。

验证参考实现：

```bash
TMP=$(mktemp -d)
cp daily/2026-10-15/solution/hitl_confirm.py "$TMP/"
cp -r daily/2026-10-15/exercise/tests "$TMP/"
cp daily/2026-10-15/exercise/main.py "$TMP/"
cd "$TMP" && python3 -m pytest -q
```
