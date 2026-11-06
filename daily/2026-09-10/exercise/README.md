# Day 36 练习说明

```bash
python3 -m pip install --user pytest
python3 -m pytest -q
python3 main.py
python3 main.py --query "前端怎么用 SSE 展示 RAG 引用" --k 2
python3 main.py --query "Prompt 里参考资料怎么拼"
```

今日重点：

1. `rag_pipeline.py` — **请你实现** TODO：规范化问题 / 转 chunk / 拼资料块 / 拼消息 / retrieve / run_rag
2. `vector_store.py`、`fake_embed`、`index_kb_dir`、`demo_generate` **已给出，勿改**
3. `main.py` — 演示已搭好：索引 `fixtures/kb/`，假生成，无网络
4. 依赖：仅 `pytest`；不要装 openai / langchain / chromadb
