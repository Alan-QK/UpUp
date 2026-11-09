# Day 10 笔记｜周挑战：多 API 聚合 CLI

## 1. 今天为什么是「周挑战」？

Week 2 不是学五堆网络碎片，而是攒齐 **Agent 调外部世界** 的地基：

| Day | 能力 | 今天用在哪 |
|-----|------|-----------|
| D6 | httpx / JSON | 两个 REST 接口 |
| D7 | 超时 / 错误分类 | 失败变 `SourceResult.error` |
| D8 | asyncio.gather | 天气 + 笑话并发 |
| D9 | 环境变量 / 脱敏 | 可选 `WEATHER_API_KEY` 注入 Header |
| D10 | **聚合 CLI** | 端到端「每日简报」 |

前端类比：你已经写了 `fetch` 封装、重试、`Promise.all`、密钥注入；今天补一个「聚合页」的命令行版。

## 2. 架构：薄 CLI + 厚 Aggregator

```text
用户敲命令
    ↓
main.py（argparse：city / --demo）
    ↓
aggregator.py（并发拉取 + 归一化 + 格式化）
    ↓
天气 API          笑话 API
（可 Mock）       （可 Mock）
```

**好习惯**：

- aggregator 不知道「怎么打印颜色」
- CLI 不知道「JSON 字段叫 temp_c 还是 temperature」
- 测试只打 aggregator（`MockTransport`，快、稳、无外网）

以后做 Agent（并行 tool call → 拼最终回复）也是同一拆法。

## 3. 两个假接口约定（练习用）

为了可测、不绑死真实厂商，今天约定路径与字段如下：

**天气** `GET {weather_base}/weather?city=Shanghai`

```json
{"city": "Shanghai", "temp_c": 28, "condition": "晴"}
```

**笑话** `GET {joke_base}/joke`

```json
{"setup": "为什么前端爱写 TypeScript？", "punchline": "因为 any 也是一种安全感。"}
```

真实世界里你会换 OpenWeather / 笑话站等；**换厂商 = 换解析函数**，聚合骨架不动。

## 4. 错误隔离：部分成功也要能出货

```text
gather(
  weather → ok / error,
  joke    → ok / error,
)
        ↓
   DailyBrief（两个 SourceResult）
        ↓
   format_brief（缺哪块就写「不可用」）
```

Agent 同理：日历工具挂了，不该让整个助手崩溃；应回报「日历暂不可用，其它任务已完成」。

## 5. 为什么 `--demo` 很重要？

学习阶段经常：

- 公司网络拦外网
- 免费 API 限流 / 抽风
- CI 不能依赖第三方可用性

所以：

1. **pytest**：全程 `MockTransport`
2. **手工**：`python3 main.py brief Shanghai --demo` 也能跑
3. 真要打外网时再去掉 `--demo`（可选作业，非今日验收）

## 6. 可选密钥 Header

若设置了环境变量 `WEATHER_API_KEY`，请求天气时带：

```http
Authorization: Bearer <key>
```

没有就不带——本地 Demo 不强制密钥。  
（练习里用注入的 `environ` dict 测，别读你本机真实 Key。）

## 7. 本周能力串线

```text
JsonClient
  → 可重试包装（稳健）
  → AsyncClient + gather（并发）
  → .env / require_env（安全）
  → 今日：多源聚合 CLI（组合）
```

下周 Day 11 起，第三个「外部世界」变成 **LLM Chat Completions**——请求形态会更熟：JSON in / JSON out，只是字段换成 `messages`。

## 8. 常见坑

| 坑 | 正确做法 |
|----|----------|
| `await` 天气完再 `await` 笑话 | 两个 coroutine 一起丢进 `gather` |
| 天气 404 直接抛到 CLI 崩掉 | 收成 `SourceResult(ok=False, error=...)` |
| 测试打真实 API | `httpx.MockTransport` |
| 把解析逻辑写进 `main.py` | 放进 aggregator，便于单测 |

## 下一步

Day 11：Chat Completions 第一次调用——把「HTTP JSON 客户端」接到大模型上。
