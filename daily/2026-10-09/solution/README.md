# Day 56 参考实现

先独立完成 `../exercise/`，再对照本目录的 `prompt_injection_lab.py`。

验证方式（把 solution 与 exercise 的 tests/main 放到同一临时目录）：

```bash
tmpdir=$(mktemp -d)
cp daily/2026-10-09/solution/prompt_injection_lab.py "$tmpdir/"
cp daily/2026-10-09/exercise/main.py "$tmpdir/"
cp -r daily/2026-10-09/exercise/tests "$tmpdir/"
cd "$tmpdir" && python3 -m pytest -q && python3 main.py --demo
```
