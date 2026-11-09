# Exercise · Day 64 记忆写入策略

## 你要完成什么

编辑 `memory_policy.py`，实现「何时写入长期记忆」的启发式：

- `normalize_candidate` / `contains_sensitive`
- `decide_write`（按文档规定的优先级返回 `MemoryDecision`）
- `decide_batch` / `filter_writable` / `summarize_decisions`
- `run_demo_policy` / `render_memory_policy_report`

正则与 `build_demo_utterances`、数据结构已给齐。

## 怎么跑

```bash
python3 -m pip install --user pytest
cd daily/2026-11-02/exercise
python3 -m pytest -q
python3 main.py --demo
python3 main.py --report
```

## 提示

1. 决策是**规则流水线**，不是 LLM：按顺序匹配，命中即返回
2. 寒暄（`_EPHEMERAL_RE`）要放在「过短」检查之前，否则「谢谢」会被误判为 too_short
3. 敏感信息一律 SKIP，不要 ASK（避免把密钥写进确认 UI）
4. ASK 只用于「像偏好但带犹豫词」的情况，交给 HITL
