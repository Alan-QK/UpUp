# Day 39 练习说明

```bash
python3 -m pip install --user pytest
python3 -m pytest -q
python3 main.py
python3 main.py --min-score 0.70
python3 main.py --k 2 --min-score 0.55
```

今日重点：

1. `rag_eval.py` — **请你实现** TODO：样例校验 / 加载 / 拒答判定 / 命中判定 / 汇总 / Markdown 报告 / run_eval
2. `rag_pipeline.py`、`vector_store.py` **已给出，勿改**（复用 Day 36）
3. `fixtures/golden/cases.json` — 8 条标定样例（5 应答 + 3 应拒）
4. `main.py` — 索引知识库 → 跑评测 → 打印报告
5. 依赖：仅 `pytest`；不要装 openai / langchain / chromadb
