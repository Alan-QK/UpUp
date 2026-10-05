# Day 40 练习说明

```bash
python3 -m pip install --user pytest   # 若尚未安装
python3 -m pytest -q
python3 main.py demo
python3 main.py ask "RAG 为什么能降低幻觉"
python3 main.py eval
```

今日重点：

1. `mini_rag.py` — **请你实现** `load_documents` / `index_documents` / `MiniRag`
2. 其余模块（chunker / vector_store / rag_pipeline / citations / refusal / rag_eval）**已给齐，勿改**
3. 测试全部本地假向量，不访问外网、不需要 API Key
4. 完成后对照 `../solution/mini_rag.py`，并把打磨版放到 `projects/mini-rag/`
