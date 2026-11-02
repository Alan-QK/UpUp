# Exercise · Day 63 长期向量记忆

## 你要完成什么

编辑 `vector_memory.py`，实现跨会话的偏好记忆：

- `_l2_normalize` / `mock_embed` / `cosine_similarity`
- `format_memory_block`
- `VectorMemoryStore`（upsert / search / 用户隔离）
- `seed_demo_store` / `render_vector_memory_report`

数据结构与 `_stable_bucket`、`build_demo_preferences` 已给齐。

## 怎么跑

```bash
python3 -m pip install --user pytest
cd daily/2026-10-29/exercise
python3 -m pytest -q
python3 main.py --demo
python3 main.py --cross
python3 main.py --report
```

## 提示

1. `mock_embed` 不要用内置 `hash()`（会受 PYTHONHASHSEED 影响），用已给的 `_stable_bucket`
2. `search` 先按 `user_id` 过滤，再算余弦，再 `min_score` 截断
3. 同分排序：`(-score, id)` 保证稳定
4. 注入块必须以 `[长期记忆]` 开头，方便前端/Agent 识别
