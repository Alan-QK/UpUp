# Day 30 练习说明

```bash
python3 -m pip install --user pytest 'pydantic>=2'
python3 -m pytest -q
python3 main.py
python3 main.py --format csv
python3 main.py --show-prompt
```

今日重点：

1. `meeting_minutes.py` — **请你实现** TODO：日期规范化、Prompt 组装、解析校验、Markdown/CSV 导出
2. `ActionItem` / `MeetingMinutes` Schema、`extract_json_object`、`schema_for_prompt` **已给出，勿改**
3. `main.py` — 演示已搭好：一份会议原文 + mock LLM → Markdown/CSV
4. 用可注入的 `complete_fn`，不要安装 openai / langchain
