# Day 7｜超时、重试与错误分类

> 日期：2026-07-29（周三）  
> Phase 1 / Week 2 · 学习日序号：**D7 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 把网络失败分成「可重试 / 不可重试」两类（Agent 调用 LLM 时天天碰到）
2. 实现带 **超时 + 有限次重试 + 退避** 的 HTTP 包装器
3. 用 MockTransport 模拟超时、502、404，验证重试策略
4. 说清楚：为什么 4xx 通常不重试，而 5xx / 超时往往要重试

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 2）
2. 昨日 [`Day 6`](../2026-07-27/README.md)（JsonClient 基础，今天在其上加重试）
3. 今日笔记：[`notes.md`](./notes.md)

重点抓住三件事：

- **错误分类先于重试**：先判断「值不值得再试」，再决定 sleep
- **有上限的重试**：`max_retries` + 退避，禁止死循环打爆 API
- **前端类比**：axios interceptor 里对 502 自动重试；对 401 直接跳登录

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user httpx pytest
```

### 任务

1. 完成 `exercise/retry_client.py` 中的 TODO（错误分类 + `RetryingJsonClient`）
2. 阅读 `exercise/main.py`（Mock 演示：先 503 再成功）
3. 跑通测试：

```bash
cd daily/2026-07-29/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] 超时 / 连接失败 / 429 / 5xx → 可重试；其他 4xx → 不重试
- [ ] 重试次数受 `max_retries` 限制，失败后抛出最后一次异常
- [ ] 成功前若中间失败过，仍能返回最终 JSON
- [ ] 退避使用 `backoff_seconds * (attempt + 1)`（简单线性即可）

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能列出至少 3 种「值得重试」的失败
- [ ] 我知道为什么 404/400 重试通常没意义
- [ ] 我理解 `max_retries=2` 表示最多额外试 2 次（总共最多 3 次请求）
- [ ] 我已知明天 Day 8：asyncio 基础与并发请求

---

## 通知摘要（便于推送）

**Day 7｜超时、重试与错误分类**  
实现可配置重试的 JSON HTTP 包装器（错误分类 + 线性退避），用 Mock 验证稳健网络层。  
路径：`daily/2026-07-29/`
