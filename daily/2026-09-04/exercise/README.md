# Day 32 练习说明

```bash
python3 -m pip install --user pytest
python3 -m pytest -q
python3 main.py
python3 main.py --size 40 --overlap 10
python3 main.py --stats
```

今日重点：

1. `chunker.py` — **请你实现** TODO：参数校验、固定窗口滑动、多文档切分、统计
2. `Chunk` / `Document` dataclass **已给出，勿改字段名**
3. `main.py` — 演示已搭好：对内置样例文本切块并打印
4. 只用标准库，不要安装 langchain / llama-index
