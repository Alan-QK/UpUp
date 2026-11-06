# Solution · Day 68

参考实现：`reflection.py`

建议先独立完成 exercise；对照时重点看：

1. 决策优先级：`abort > revise > retry > accept`
2. `skipped` → `revise`；空/短观察与 `failed` → `retry`
3. `run_reflection`：最后一轮若仍需 retry → `abort` 且 **不** `apply_retry`
4. 级联失败（failed + 多步 skipped）应 `revise`，不要盲重试
5. 报告二级标题必须与 `REQUIRED_REPORT_SECTIONS` 一致
