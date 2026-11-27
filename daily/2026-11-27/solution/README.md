# Day 72 参考实现

先自己完成 `../exercise/` 再对照本目录的 `pipeline_agents.py`。

验证（把 solution 模块与 exercise 测试放到同一临时目录）：

```bash
tmpdir=$(mktemp -d)
cp daily/2026-11-27/solution/pipeline_agents.py "$tmpdir/"
cp -r daily/2026-11-27/exercise/tests "$tmpdir/"
cp daily/2026-11-27/exercise/main.py "$tmpdir/"
cd "$tmpdir" && python3 -m pytest -q
```
