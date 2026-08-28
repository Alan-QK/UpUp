# 今日学习推送

> 更新日期：2026-08-28  
> 学习日：Day **27** / 120 · Phase 2 · Week 6

## 主题

**校验失败重试**

## 今日要做什么

1. 阅读笔记：[`daily/2026-08-28/notes.md`](./daily/2026-08-28/notes.md)
2. 完成练习：[`daily/2026-08-28/`](./daily/2026-08-28/)
3. 安装依赖：`python3 -m pip install --user 'pydantic>=2'`
4. 跑通：`cd daily/2026-08-28/exercise && python3 -m pytest -q`
5. 手工试跑：`python3 main.py --demo`（可加 `--fail-twice` / `--always-bad`）

## 一句话练习

实现结构化输出 repair loop：校验失败后把错误摘要喂回模型，最多修复重试 3 次。

## 进度

详见 [`.automation/progress.json`](./.automation/progress.json)
