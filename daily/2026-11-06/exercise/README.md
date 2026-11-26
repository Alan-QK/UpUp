# Exercise · Day 68 Reflection 反思纠错

## 你要改的文件

- `reflection.py`：所有 TODO

## 已给齐

- `StepSnapshot` / `RunSnapshot` / `Critique` / `ReflectionRound` / `ReflectionResult`
- 决策常量与 `DECISION_PRIORITY`、issue 标签、`PASS_SCORE` / `MIN_OBS_LEN`
- `_improved_observation` 辅助函数（模拟重试观察）
- `main.py`：CLI（`--case` / `--demo` / `--report`）
- `tests/test_reflection.py`：验收测试

## 建议顺序

1. `score_step` / `critique_step` / `critique_run`
2. `pick_overall_decision`
3. `improve_step` / `find_retry_targets` / `apply_retry`
4. `run_reflection`（先 accept / revise，再 retry 与 abort）
5. sample / demo / `summarize_reflection` / `render_*`

## 跑测试

```bash
cd daily/2026-11-06/exercise
python3 -m pytest -q
```
