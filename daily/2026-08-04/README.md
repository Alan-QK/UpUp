# Day 11｜Chat Completions 第一次调用

> 日期：2026-08-04（周二）  
> Phase 1 / Week 3 · 学习日序号：**D11 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清 OpenAI 兼容 **Chat Completions** 请求/响应长什么样
2. 用 `httpx` 发起一次**非流式**对话（`stream=false`）
3. 从响应里安全取出 `choices[0].message.content` 与用量字段
4. 用 `MockTransport` 离线测通；有真实 Key 时也能打一次真接口

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 3）
2. 今日笔记：[`notes.md`](./notes.md)
3. 仓库 [`.env.example`](../../.env.example)（回顾密钥变量名）

重点抓住三件事：

- **协议比 SDK 重要**：先会手写 JSON POST，再谈官方 SDK
- **messages 是会话状态**：今天只做单轮；多轮是 Day 12
- **永远 Mock 可测**：不要让单测依赖外网与真实计费

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 任务

封装一个最小 `ChatClient`：向 `{base_url}/chat/completions` 发非流式请求，解析助手回复。

1. 完成 `exercise/chat_client.py` 中的 TODO
2. 阅读 `exercise/main.py`（`--demo` 离线；有环境变量时可真调）
3. 跑通测试：

```bash
cd daily/2026-08-04/exercise
python3 -m pytest -q
```

若尚未安装 httpx：

```bash
python3 -m pip install --user httpx
```

4. 手工试跑（离线 Demo）：

```bash
python3 main.py --demo
python3 main.py --demo -m "用一句话介绍 AI Agent"
```

有真实 Key 时（可选，勿提交 `.env`）：

```bash
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.openai.com/v1   # 或兼容网关
export OPENAI_MODEL=gpt-4o-mini
python3 main.py -m "你好"
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `complete` 发送 `POST /chat/completions`，Body 含 `model`、`messages`、`stream: false`
- [ ] Header 带 `Authorization: Bearer <api_key>`
- [ ] 成功时返回 `ChatCompletionResult`（至少含 `content`、`model`）
- [ ] 非 2xx / 非法 JSON / 缺 choices → 抛出约定异常
- [ ] `--demo` 不访问外网即可打印助手回复

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能默写出 Chat Completions 请求 JSON 的核心字段
- [ ] 我知道 `base_url` 通常以 `/v1` 结尾，path 是 `/chat/completions`
- [ ] 我能解释：为什么今天不引入官方 SDK，而是手写 httpx
- [ ] 我已知明天 Day 12：角色消息与多轮上下文

---

## 通知摘要（便于推送）

**Day 11｜Chat Completions 第一次调用**  
手写非流式对话客户端：POST `/chat/completions`，解析助手回复；Mock 离线可测。  
路径：`daily/2026-08-04/`
