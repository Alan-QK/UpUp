# Exercise · Day 67 Plan-and-Execute

## 你要改的文件

- `executor.py`：所有 TODO

## 已给齐

- `Plan` / `PlanStep` / `ToolSpec` / `StepResult` / `ExecutionState` 数据类
- `KIND_TO_TOOL` 映射与 mock 工具函数（`_tool_*`）
- `main.py`：CLI（`--goal` / `--demo` / `--report`）
- `tests/test_executor.py`：验收测试

## 建议顺序

1. `kind_to_tool_name` / `deps_satisfied`
2. `default_tool_registry` / `invoke_tool`
3. `execute_plan`（先 happy path，再 failure / max_steps）
4. `build_sample_plan` / demo / `summarize_execution` / `render_*`

## 跑测试

```bash
cd daily/2026-11-05/exercise
python3 -m pytest -q
```
