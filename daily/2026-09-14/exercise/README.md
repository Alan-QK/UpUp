# Day 38 练习说明

```bash
python3 -m pip install --user pytest
python3 -m pytest -q
python3 main.py
python3 main.py --query "今天天气怎么样"
python3 main.py --query "RAG 为什么能降低幻觉" --min-score 0.55
python3 main.py --min-score 0.75 --min-margin 0.05 --query "Python dataclass"
```

今日重点：

1. `refusal.py` — **请你实现** TODO：策略校验 / top 分与 margin / 门控 / 拒答文案 / gated_answer
2. `rag_pipeline.py`、`vector_store.py` **已给出，勿改**（复用 Day 36）
3. `main.py` — 演示：相关问题放行假生成，跑题问题拒答且不调用生成
4. 依赖：仅 `pytest`；不要装 openai / langchain / chromadb
