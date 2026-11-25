# Solution · Day 69

参考实现：`state_machine.py`

建议先独立完成 exercise；对照时重点看：

1. 转移表驱动：`(source, event) → target`，非法转移抛 `IllegalTransitionError`
2. `hitl_approved` **不进静态表**，靠 `hitl_resume` 动态恢复
3. Day 68 决策通过 `map_reflection_decision` 变成事件
4. Mermaid 必须由同一份 `default_transitions()` + `HITL_RESUME_DEFAULT` 生成
5. 报告二级标题必须与 `REQUIRED_REPORT_SECTIONS` 一致
