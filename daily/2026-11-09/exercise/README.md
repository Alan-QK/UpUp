# Exercise · Day 69 状态机视角

## 你要改的文件

- `state_machine.py`：所有 TODO

## 已给齐

- 七态 / 事件常量、`Transition` / `TransitionRecord`、`HITL_RESUME_DEFAULT`
- `DECISION_TO_EVENT`、`REQUIRED_REPORT_SECTIONS`、`IllegalTransitionError`
- `main.py`：CLI（`--case` / `--demo` / `--diagram` / `--report`）
- `tests/test_state_machine.py`：验收测试

## 建议顺序

1. `default_transitions` / `build_transition_map` / `can_transition` / `lookup_transition`
2. `map_reflection_decision`
3. `AgentStateMachine.send`（先主路径，再 HITL 动态恢复）
4. `simulate_*` / `apply_events` / `summarize_machine` / `render_trace`
5. `render_mermaid`（含 hitl_approved 展开边）/ `render_state_machine_report`

## 跑测试

```bash
cd daily/2026-11-09/exercise
python3 -m pytest -q
```
