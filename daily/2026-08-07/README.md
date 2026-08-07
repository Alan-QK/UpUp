# Day 14｜Token 与成本意识

> 日期：2026-08-07（周五）  
> Phase 1 / Week 3 · 学习日序号：**D14 / 120**  
> 建议时长：**75 分钟**（概念 20 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 解释 prompt / completion / total tokens 分别指什么
2. 用「百万 token 单价」算出单次调用的美元费用
3. 实现本地 **token 估算**（无 usage 时的兜底）
4. 维护一个 `UsageLedger`，为每次调用打可读的用量/费用日志

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 3）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾 Day 11 的 `usage` 字段：[`daily/2026-08-04/notes.md`](../2026-08-04/notes.md)

重点抓住三件事：

- **Token ≠ 字符**：中英混合时别用「字数」当账单
- **优先 API `usage`，缺失再估算**
- **输出单价通常更高**；Agent 多步会放大账单

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 任务

实现用量账本与费用计算（纯逻辑为主；可选接 Day 11 客户端）。

1. 完成 `exercise/usage_meter.py` 中的 TODO
2. `chat_client.py` **已给齐**（Day 11 完成版），真调/Mock 时用来取 `usage`
3. 跑通测试：

```bash
cd daily/2026-08-07/exercise
python3 -m pytest -q
```

若要用 `--live` / Mock 聊天路径且尚未安装 httpx：

```bash
python3 -m pip install --user httpx
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --demo --with-chat
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `estimate_tokens` 符合笔记中的 CJK / 非 CJK 规则
- [ ] `calculate_cost_usd` 按百万 token 计价，结果保留 8 位小数
- [ ] API 双边 usage 齐全时 `source="api"`；否则估算并标 `source="estimate"`
- [ ] `format_log_line` / `format_summary` 可读且字段齐全
- [ ] 负 token 数抛 `ValueError`

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能口述一次调用的费用公式
- [ ] 我知道为什么多轮对话会让 prompt_tokens 变贵
- [ ] 我不会把本地估算当成向财务报销的依据
- [ ] 我已知下周 Day 15：多轮对话 CLI 周挑战

---

## 通知摘要（便于推送）

**Day 14｜Token 与成本意识**  
实现 token 估算、按价目表计费与 UsageLedger 日志：优先 API usage，缺失再估算。  
路径：`daily/2026-08-07/`
