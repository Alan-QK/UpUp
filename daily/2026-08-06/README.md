# Day 13｜流式输出

> 日期：2026-08-06（周四）  
> Phase 1 / Week 3 · 学习日序号：**D13 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说明 Chat Completions **流式**与非流式的请求/响应差异（`stream: true` + SSE）
2. 解析 `data: {...}` 行，取出 `choices[0].delta.content`
3. 用 httpx **流式读取**并逐块 `yield` 文本
4. 在终端边收边打印（`flush`），拼出完整回复

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 3）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾 Day 11 非流式：[`daily/2026-08-04/notes.md`](../2026-08-04/notes.md)

重点抓住三件事：

- **流式 = 同一接口，`stream: true`，响应变 SSE 文本流**
- **增量在 `delta.content`，不是 `message.content`**
- **终端体验靠逐块 print + flush**；完整文本自己拼接

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 任务

实现 OpenAI 兼容的**流式** Chat 客户端，并做终端边打字边打印。

1. 阅读 `exercise/streaming_client.py` 顶部约定与已给齐的构造器
2. 完成其中的 TODO（SSE 解析、`iter_content`、`print_stream`）
3. 跑通测试：

```bash
cd daily/2026-08-06/exercise
python3 -m pytest -q
```

若尚未安装 httpx：

```bash
python3 -m pip install --user httpx
```

4. 手工试跑（离线 Demo）：

```bash
python3 main.py --demo
python3 main.py --demo -m "用一句话解释什么是 SSE"
```

有真实 Key 时（可选，勿提交 `.env`）：

```bash
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_MODEL=gpt-4o-mini
python3 main.py -m "写一句欢迎语，稍长一点"
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] 请求体含 `"stream": true`
- [ ] 能解析多行 SSE，并在 `[DONE]` 处停止
- [ ] 只产出 `delta.content` 为字符串的片段（跳过无 content 的 chunk）
- [ ] `print_stream` 边打印边 flush，并返回拼接全文
- [ ] `--demo` 能看到文字逐块出现（或至少立即刷出）

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能对比画出非流式 JSON vs 流式 SSE 的形态
- [ ] 我知道为什么要用 `client.stream(...)` 而不是一次 `resp.json()`
- [ ] 我能解释 `data: [DONE]` 的作用
- [ ] 我已知明天 Day 14：Token 与成本意识

---

## 通知摘要（便于推送）

**Day 13｜流式输出**  
实现 SSE 解析与流式终端打印：`stream: true` → 逐块取出 `delta.content` 并 flush 输出。  
路径：`daily/2026-08-06/`
