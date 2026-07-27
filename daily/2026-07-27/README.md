# Day 6｜HTTP 与 httpx

> 日期：2026-07-27（周一）  
> Phase 1 / Week 2 · 学习日序号：**D6 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 用前端熟悉的「请求 / 响应 / JSON」心智模型理解 Python HTTP
2. 用 `httpx` 发起 GET / POST，并正确设置 timeout
3. 封装一个小的 **JSON HTTP 客户端**（为后续调 LLM API 铺路）
4. 用 `httpx.MockTransport` 写不依赖外网的单元测试

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 2 小节）
2. 今日笔记：[`notes.md`](./notes.md)

重点抓住三件事：

- **httpx ≈ fetch + axios**：同步 API 先够用，异步下周再上
- **永远设 timeout**：Agent 调外部 API 时，无超时 = 挂死
- **客户端封装**：`base_url` + `get_json` / `post_json`，业务代码别直接散落 `httpx.get`

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user httpx pytest
```

### 任务

1. 完成 `exercise/json_client.py` 中的 TODO（`JsonClient` + 异常）
2. 阅读 `exercise/main.py`（用 MockTransport 演示，无需外网）
3. 跑通测试：

```bash
cd daily/2026-07-27/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `get_json` / `post_json` 能解析 JSON 并返回 Python 对象
- [ ] 非 2xx 抛出 `HttpStatusError`（带 `status_code`）
- [ ] 响应不是合法 JSON 时抛出 `HttpResponseError`
- [ ] 客户端支持 `with JsonClient(...) as client:` 并正确关闭

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能用一句话对比 `fetch` 与 `httpx.get`
- [ ] 我知道为什么 LLM / Agent 调用必须设置 timeout
- [ ] 我理解 `base_url` + path 的拼接方式
- [ ] 我已知明天 Day 7：超时、重试与错误分类

---

## 通知摘要（便于推送）

**Day 6｜HTTP 与 httpx**  
封装 GET/POST JSON 客户端（含超时、状态码错误、Mock 测试），为调 LLM API 铺路。  
路径：`daily/2026-07-27/`
