# Day 29 练习说明

```bash
python3 -m pip install --user pytest 'pydantic>=2'
python3 -m pytest -q
python3 main.py
python3 main.py --format csv
python3 main.py --fail-one
```

今日重点：

1. `batch_extract.py` — **请你实现** TODO：`build_extract_messages` / `parse_contact` / `extract_one` / `extract_batch` / `contacts_to_json` / `contacts_to_csv` / `batch_summary` 等
2. `Contact` Schema、`extract_json_object`、`schema_for_prompt` **已给出，勿改**
3. `main.py` — 演示已搭好：三份名片文本 + mock LLM → JSON/CSV
4. 用可注入的 `complete_fn`，不要安装 openai / langchain
