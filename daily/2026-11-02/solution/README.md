# Solution · Day 64 记忆写入策略

参考实现：`memory_policy.py`。

先自己完成 `exercise/`；卡住再对照本目录。验证方式：

```bash
tmpdir=$(mktemp -d)
cp daily/2026-11-02/solution/memory_policy.py "$tmpdir/"
cp daily/2026-11-02/exercise/main.py "$tmpdir/"
cp -r daily/2026-11-02/exercise/tests "$tmpdir/"
cd "$tmpdir" && python3 -m pytest -q
```
