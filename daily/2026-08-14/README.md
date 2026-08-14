# Day 19｜结构化日志与调试

> 日期：2026-08-14（周五）  
> Phase 1 / Week 4 · 学习日序号：**D19 / 120**  
> 建议时长：**75 分钟**（概念 20 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清「`print` 调试」和「结构化日志」的差别，以及为什么 Agent 更需要后者
2. 实现一行一条 JSON 的 `StructuredLogger`（可注入 sink / 时钟，便于单测）
3. 在聊天请求前后打出 `chat.request` / `chat.response` / `chat.error` 事件
4. 对密钥类字段自动脱敏，避免日志变成泄密渠道

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 4）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾：Day 9 的 `mask_secret`、Day 14 的 usage 记账——今天把「可观察」做成统一事件流

重点抓住三件事：

- **事件有名字**：`event` 字段比自由文本好检索
- **字段可机读**：JSON 一行一条，后期可进 ELK / Loki / 本地 jq
- **密钥永不落盘明文**：日志里也要脱敏

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 任务

1. 完成 `exercise/chat_logger.py` 中的 TODO
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-08-14/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --demo --fail
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] 每条日志是**单行 JSON**，至少含 `ts` / `level` / `event`
- [ ] `mask_value` / 自动脱敏对 `api_key`、`*_secret`、`*_token` 等字段生效
- [ ] `log_chat_turn` 成功时打 request+response；失败时打 request+error（且向上抛出原异常）
- [ ] 测试可注入假时钟与内存 sink，不依赖真实时间与文件系统
- [ ] 全程标准库（不要引入 loguru / structlog）

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能解释：为什么 Agent 调试要靠「事件轨迹」而不是散落的 print
- [ ] 我知道 `level` 与 `event` 各自解决什么问题
- [ ] 我不会把完整 API Key 打进日志或截图
- [ ] 我已知明天 Day 20：里程碑 `cli-chatbot`（把本周能力拼进一个可演示 CLI）

---

## 通知摘要（便于推送）

**Day 19｜结构化日志与调试**  
为聊天 CLI 加 JSON 结构化日志：request/response/error 事件 + 密钥脱敏；可观测雏形。  
路径：`daily/2026-08-14/`
