# Day 10｜周挑战：多 API 聚合 CLI

> 日期：2026-08-03（周一）  
> Phase 1 / Week 2 · 学习日序号：**D10 / 120**  
> 建议时长：**90 分钟**（概念 20 + Coding 65 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 把本周学过的 **httpx / 重试思维 / asyncio / 环境变量** 拼成一个可运行小工具
2. **并发**拉取 2 个不同 API，再聚合成一份可读摘要
3. 单个源失败时仍能输出「部分成功」结果（错误隔离）
4. 用 `MockTransport` 离线跑通 pytest 与手工 Demo（不依赖外网）

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 2 回顾）
2. 今日笔记：[`notes.md`](./notes.md)

重点抓住三件事：

- **聚合 = gather + 归一化**：并发取数，再变成统一的 `DailyBrief`
- **部分失败可接受**：天气挂了仍可显示笑话（Agent 调多工具同理）
- **本周收口**：HTTP → 重试 → 异步 → 密钥 → 今天端到端串起来

---

## Coding 练习（65 分钟）

目录：[`exercise/`](./exercise/)

### 任务

实现一个「每日简报」CLI：并发拉取**天气**与**笑话**两个接口，打印摘要。

1. 完成 `exercise/aggregator.py` 中的 TODO
2. 阅读并可选微调 `exercise/main.py`（argparse + `--demo` 已搭好）
3. 跑通测试：

```bash
cd daily/2026-08-03/exercise
python3 -m pytest -q
```

若尚未安装 httpx：

```bash
python3 -m pip install --user httpx
```

4. 手工试跑（离线 Demo，不访问真实外网）：

```bash
python3 main.py brief Shanghai --demo
python3 main.py brief Tokyo --demo
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `build_daily_brief` 并发请求天气 + 笑话（用 `asyncio.gather`）
- [ ] 任一源失败时，另一源结果仍出现在摘要里
- [ ] `format_brief` 输出人类可读文本
- [ ] CLI 支持 `brief <city>`；`--demo` 用 Mock，无需外网
- [ ] 你能用一句话说明：为什么 Agent 多工具调用也需要「错误隔离」

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能解释：同步串行 vs `asyncio.gather` 在总耗时上的差别
- [ ] 我知道为什么测试 / `--demo` 要用 `MockTransport`，而不是打真实天气网
- [ ] 本周 5 天知识点我能串成一条线（见笔记末尾）
- [ ] 我已知下周 Day 11：Chat Completions 第一次调用

---

## 通知摘要（便于推送）

**Day 10｜周挑战：多 API 聚合 CLI**  
并发聚合天气 + 笑话，输出每日简报；Mock 离线可测，复用本周 HTTP/异步能力。  
路径：`daily/2026-08-03/`
