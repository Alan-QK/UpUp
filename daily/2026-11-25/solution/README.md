# Day 70 参考实现

先自己完成 `../exercise/`。卡住超过 25 分钟再对照本目录的 `research_pipeline.py`。

验证（勿直接改 exercise 交卷）：

```bash
TMP=$(mktemp -d)
cp solution/research_pipeline.py "$TMP/"
cp exercise/main.py "$TMP/"
cp -r exercise/tests "$TMP/"
cd "$TMP" && python3 -m pytest -q
```
