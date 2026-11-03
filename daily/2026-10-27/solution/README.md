# Solution · Day 61

参考实现见 `memory_window.py`。

验证：

```bash
tmpdir=$(mktemp -d)
cp daily/2026-10-27/solution/memory_window.py "$tmpdir/"
cp -r daily/2026-10-27/exercise/tests "$tmpdir/"
cp daily/2026-10-27/exercise/main.py "$tmpdir/"
cd "$tmpdir" && python3 -m pytest -q
```
