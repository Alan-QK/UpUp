# Day 34 练习说明

```bash
python3 -m pip install --user pytest
python3 -m pytest -q
python3 main.py
python3 main.py --k 2
python3 main.py --query "向量检索怎么做 top-k"
```

今日重点：

1. `vector_store.py` — **请你实现** TODO：余弦相似度、MiniCollection.add / query / count
2. 异常类 / dataclass **已给出，勿改字段名**
3. `main.py` — 演示已搭好：内置伪向量，不访问外网、不装 chromadb
4. 依赖：仅 `pytest`（标准库实现逻辑）
