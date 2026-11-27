# Solution · Day 62

参考实现见 `summary_memory.py`。

验证：

```bash
tmpdir=$(mktemp -d)
cp daily/2026-10-28/solution/summary_memory.py "$tmpdir/"
cp -r daily/2026-10-28/exercise/tests "$tmpdir/"
cp daily/2026-10-28/exercise/main.py "$tmpdir/"
cd "$tmpdir" && python3 -m pytest -q
```
