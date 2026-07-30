# Day 8｜asyncio 基础

> 日期：2026-07-30（周四）  
> Phase 1 / Week 2 · 学习日序号：**D8 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清 `async` / `await` 与「多线程」的差别（单线程协作式并发）
2. 用 `asyncio.gather` 并发发起多个 HTTP 请求并汇总结果
3. 用 `httpx.AsyncClient` + MockTransport 写可测的异步代码
4. 建立直觉：Agent 并行调多个工具 ≈ `gather` 一组协程

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 2）
2. 昨日 [`Day 7`](../2026-07-29/README.md)（稳健同步客户端；今天换成异步并发）
3. 今日笔记：[`notes.md`](./notes.md)

重点抓住三件事：

- **`await` 让出执行权**：等 I/O 时别傻阻塞整条事件循环
- **`gather` = Promise.all**：一次等一组任务，顺序与入参对齐
- **前端类比**：`async/await` + `Promise.all`；不是开一堆 Web Worker

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user httpx pytest
```

### 任务

1. 完成 `exercise/async_fetcher.py` 中的 TODO（`fetch_one` + `fetch_many`）
2. 阅读 `exercise/main.py`（Mock 演示：并发拉 3 个接口）
3. 跑通测试：

```bash
cd daily/2026-07-30/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `fetch_many` 对 3 个 path 并发请求，返回与入参**同序**的结果列表
- [ ] 单个 path 失败不影响其他 path（该条 `ok=False`，其余照常）
- [ ] 使用 `httpx.AsyncClient`（不要用同步 `httpx.Client` 假装并发）
- [ ] 测试全部离线（MockTransport），不依赖外网

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能用一句话解释：为什么 I/O 密集适合 asyncio，CPU 密集不一定
- [ ] 我知道 `gather` 与「一个 for 循环里顺序 await」的耗时差别
- [ ] 我能指出 Agent「并行工具调用」和今天 Demo 的对应关系
- [ ] 我已知明天 Day 9：环境变量与密钥管理（`.env`）

---

## 通知摘要（便于推送）

**Day 8｜asyncio 基础**  
用 `asyncio.gather` + `httpx.AsyncClient` 并发请求 3 个 URL 并汇总，建立 Agent 并行工具调用直觉。  
路径：`daily/2026-07-30/`
