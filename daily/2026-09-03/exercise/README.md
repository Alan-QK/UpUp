# Day 31 练习说明

```bash
python3 -m pip install --user pytest
python3 -m pytest -q
python3 main.py
python3 main.py --stats
python3 main.py --show note.md
```

今日重点：

1. `doc_loader.py` — **请你实现** TODO：换行/BOM/空行/frontmatter/注释清洗 + 目录扫描 + 加载
2. `Document` dataclass 与 `SUPPORTED_SUFFIXES` **已给出，勿改字段名**
3. `main.py` — 演示已搭好：加载 `fixtures/` 语料并打印摘要
4. 只用标准库，不要安装 langchain / unstructured
