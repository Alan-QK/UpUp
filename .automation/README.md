# 自动化约定（供每日 Cloud Agent 使用）

## 目标

每个工作日（周一至周五，Asia/Shanghai 约 10:00）自动生成并推送：

1. 当日学习内容与 Coding 练习 → `daily/YYYY-MM-DD/`
2. 更新 `.automation/progress.json`
3. Commit + Push 到当前开发分支
4. 如需则更新 PR

## 生成前必读

1. `curriculum/00-总纲.md`
2. 对应 `curriculum/phases/phase-0X-*.md`
3. `.automation/progress.json`
4. `.automation/day-index.json`（日序号 → 主题映射）
5. 本文件

## 跳过规则

- 周六、周日：不生成新 Day（可写一句「周末休息」备注，但默认直接跳过）
- 若 `last_pushed_date == 今天`：不要重复推送同一天
- 若 `current_day_index > total_learning_days`：标记 `status=completed`，推送结营总结

## 每日产出结构（必须）

```text
daily/YYYY-MM-DD/
  README.md      # 今日目标、时长、练习、自检
  notes.md       # 精炼笔记
  exercise/      # 可运行起始代码
  solution/      # 参考实现（鼓励先做再看）
```

## 内容质量要求

- 全程中文
- 面向「高级前端 + Python 薄弱」读者，避免无必要黑话；必要术语给一句话解释
- 练习必须可运行（允许 mock LLM）
- 明确预计时长（合计约 60–90 分钟）
- 每天结束有自检清单（3–5 条）
- 与当日 `day-index` 主题对齐，不要跳周乱序

## Commit 信息格式

```text
docs(daily): Day N - <主题> (YYYY-MM-DD)
```

初始化总纲：

```text
docs(curriculum): 添加前端到 AI Agent 半年转型总纲与阶段规划
```
