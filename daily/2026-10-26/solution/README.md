# Solution · Day 60

完整参考实现。请先独立完成 `exercise/tool_agent.py`，再对照本目录。

验证方式（复制到临时目录与 tests 合并后运行）：

```bash
TMP=$(mktemp -d)
cp daily/2026-10-26/solution/*.py "$TMP/"
cp daily/2026-10-26/exercise/main.py "$TMP/"
cp -r daily/2026-10-26/exercise/tests "$TMP/"
cp -r daily/2026-10-26/exercise/sample_workspace "$TMP/"
cd "$TMP" && python3 -m pytest -q
```
