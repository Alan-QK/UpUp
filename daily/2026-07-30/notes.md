# Day 8 笔记｜asyncio 基础

## 1. 今天学什么？

前两天你写的是**同步** HTTP：一次请求结束，再发下一次。  
Agent 场景里经常要**同时**做几件事：

- 并行调用 3 个工具
- 同时拉向量库 + 查日历 + 读配置
- 对多个文档分片并发 embedding

同步串行会把总耗时加成「各项之和」。  
`asyncio` 让你在**等网络**时去推进别的任务——总耗时接近「最慢那一项」。

| 前端直觉 | Python |
|----------|--------|
| `async/await` | 同名关键字，语义几乎一样 |
| `Promise.all([...])` | `asyncio.gather(...)` |
| 单线程事件循环（浏览器主线程 + microtask） | `asyncio` 事件循环 |
| Web Worker / 多线程 | 那是另一条路（`threading` / `multiprocessing`），今天不走 |

## 2. 最小心智模型

```text
协程（coroutine）= 可暂停的函数
  async def fetch(...): ...
      data = await client.get(...)   # 等 I/O，把 CPU 让给别人
      return data

事件循环 = 调度员
  谁 await 了就挂起；谁就绪了就继续跑
```

一句话：

> **asyncio 擅长「大量等待」；不擅长「大量算」.**

算得猛（压缩、纯 Python 热循环）会堵死事件循环——那时候才考虑线程/进程。Agent 调 API 主要是等待，所以 asyncio 很合适。

## 3. `gather`：并发汇总

```python
import asyncio
import httpx

async def fetch(client: httpx.AsyncClient, path: str) -> dict:
    r = await client.get(path)
    r.raise_for_status()
    return r.json()

async def main() -> None:
    async with httpx.AsyncClient(base_url="https://api.example", timeout=5.0) as client:
        a, b, c = await asyncio.gather(
            fetch(client, "/a"),
            fetch(client, "/b"),
            fetch(client, "/c"),
        )
        print(a, b, c)

asyncio.run(main())
```

对比错误写法（看起来像异步，其实串行）：

```python
a = await fetch(client, "/a")
b = await fetch(client, "/b")  # 等 a 完了才开始
c = await fetch(client, "/c")
```

## 4. 失败怎么处理？

`gather` 默认：**任意一个抛错 → 整个 gather 抛错**（其它任务可能还在跑，但你拿不到整齐结果）。

Agent 更常见的需求是：**单工具失败，其它结果照收**。做法：

1. 在每个子任务内部 `try/except`，返回 `ok=False` 的结果对象（今天练习采用）
2. 或 `asyncio.gather(..., return_exceptions=True)`，自己把 Exception 归一化

今天练习用方案 1，类型更清晰，也更贴近「工具调用结果列表」。

## 5. httpx 异步客户端

```python
async with httpx.AsyncClient(base_url=..., timeout=..., transport=...) as client:
    resp = await client.get("/v1/x")
```

注意：

- 同步 `Client` 与异步 `AsyncClient` **不要混用**
- 测试继续用 `MockTransport`（Day 6/7 同款），无需外网
- `pytest` 里用 `asyncio.run(...)` 包一层即可，今天不引入 `pytest-asyncio`

## 6. 和 Agent 的关系

```text
用户目标
  → Agent 决定并行调 tool_a / tool_b / tool_c
  → gather(三个工具协程)
  → 把结果列表塞回上下文，再让模型综合
```

你前端写过「同时请求用户信息 + 权限 + 配置再渲染」——同一套并发直觉，换到 Agent Loop 而已。

## 7. 今日一句话

> 并发 I/O = `async` 函数 + `await` 让出 + `gather` 汇总；失败要隔离，别让一个工具拖垮整批。

## 8. 明日预告

Day 9：环境变量与密钥管理——实现 `.env` 加载，API Key 永不写进代码。

---

## 我的记录（请自己填写）

1.  
2.  
3.  
