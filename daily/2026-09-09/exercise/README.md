# Day 35 练习说明

```bash
python3 -m pip install --user pytest
python3 -m pytest -q
python3 main.py
python3 main.py --query "前端 SSE 怎么展示引用" --k 2
python3 main.py --query "Python pytest 与 dataclass"
```

今日重点：

1. `notes_search.py` — **请你实现** TODO：发现/加载/切分/建索引/检索/格式化
2. `vector_store.py`（Day 34 MiniCollection）与 `fake_embed` **已给出，勿改**
3. `main.py` — 演示已搭好：扫描 `fixtures/notes/`，伪向量，无网络
4. 依赖：仅 `pytest`（标准库实现逻辑）；不要装 chromadb / openai / langchain
