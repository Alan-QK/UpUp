# Exercise · Day 66 任务分解 Planner

## 你要改的文件

- `planner.py`：所有 TODO

## 已给齐

- `main.py`：CLI（`--goal` / `--demo` / `--report`）
- `tests/test_planner.py`：验收测试
- 正则与常量：分类规则已写死，勿改语义

## 建议顺序

1. `normalize_goal` / `classify_goal` / `estimate_complexity`
2. `_clamp_max_steps` / `_templates` / `_build_steps`
3. `plan_from_goal`
4. `render_plan` / demo / `summarize_plans` / `render_planner_report`

## 跑测试

```bash
cd daily/2026-11-04/exercise
python3 -m pytest -q
```
