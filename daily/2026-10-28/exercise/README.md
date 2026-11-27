# Exercise · Day 62 摘要记忆

## 你要完成什么

编辑 `summary_memory.py`，实现超长对话的滚动摘要：

- `estimate_tokens` / `format_summary_message` / `is_summary_message`
- `default_summarize`（确定性 mock）
- `compact_exchanges`
- `SummarizingMemory`
- `render_summary_report`

`build_demo_exchanges` 与数据结构已给齐。

## 怎么跑

```bash
python3 -m pip install --user pytest
cd daily/2026-10-28/exercise
python3 -m pytest -q
python3 main.py --demo
python3 main.py --roll
python3 main.py --report
```

## 提示

1. 先写 `default_summarize` 的截断与「近期折叠」拼接
2. `compact_exchanges`：轮数未超限就原样组装；超了再 `summarizer(folded, previous)`
3. 消息顺序固定：system → 摘要 system → 最近轮
4. `SummarizingMemory.add_exchange` 每次都跑 compact，并把内部 exchanges 收成 recent
