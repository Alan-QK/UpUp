# Day 37 练习说明

```bash
python3 -m pip install --user pytest
python3 -m pytest -q
python3 main.py
python3 main.py --query "前端怎么用 SSE 展示引用" --k 2
python3 main.py --mode all --query "Prompt 参考资料怎么编号"
```

今日重点：

1. `citations.py` — **请你实现** TODO：snippet / 解析 `[N]` / 筛选 / 格式化来源 / 组装 CitedAnswer
2. `rag_pipeline.py`、`vector_store.py` **已给出，勿改**（复用 Day 36）
3. `main.py` — 演示：假生成末尾带 `[1]`，再打印带「来源」区块的答案
4. 依赖：仅 `pytest`；不要装 openai / langchain / chromadb
