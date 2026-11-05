# Day 58 参考实现

先完成 `../exercise/` 再对照本目录的 `mock_llm_agent.py`。

验证方式（推荐复制到临时目录与测试一起跑）：

```bash
TMP=$(mktemp -d)
cp daily/2026-10-14/solution/mock_llm_agent.py "$TMP/"
cp -r daily/2026-10-14/exercise/tests "$TMP/"
cp daily/2026-10-14/exercise/main.py "$TMP/"
cd "$TMP" && python3 -m pytest -q
```
