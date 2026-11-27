# Solution · Day 67

参考实现：`executor.py`

建议先独立完成 exercise；对照时重点看：

1. `deps_satisfied` 只认 `STATUS_DONE`（FAILED 不算满足）
2. `stop_on_failure` 时：FAILED → 后续 `skipped` + `stop_reason=failed`
3. `max_steps` 计的是**实际工具调用**（含失败调用），不含 skip
4. 报告二级标题必须与 `REQUIRED_REPORT_SECTIONS` 一致
