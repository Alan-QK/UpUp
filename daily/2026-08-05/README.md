# Day 12｜角色消息与多轮上下文

> 日期：2026-08-05（周三）  
> Phase 1 / Week 3 · 学习日序号：**D12 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 分清 `system` / `user` / `assistant` 各自职责
2. 理解 Chat API **无状态**：多轮靠本地拼完整 `messages`
3. 实现带固定人设的 `PersonaAssistant`（ask / reset / history）
4. 用 Mock 验证「第二轮请求包含第一轮对话」

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 3）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾 Day 11：[`daily/2026-08-04/notes.md`](../2026-08-04/notes.md)

重点抓住三件事：

- **system = 产品规则**，不是用户闲聊
- **历史必须回传**，否则模型没有「记忆」
- **状态在你这边**：助手类负责拼装与追加

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 任务

在已给齐的 `ChatClient` 之上，实现角色化多轮助手。

1. 阅读 `exercise/chat_client.py`（已完成，无需改）
2. 完成 `exercise/persona_assistant.py` 中的 TODO
3. 跑通测试：

```bash
cd daily/2026-08-05/exercise
python3 -m pytest -q
```

若尚未安装 httpx：

```bash
python3 -m pip install --user httpx
```

4. 手工试跑（离线 Demo）：

```bash
python3 main.py --demo
python3 main.py --demo -m "什么是 system 角色？" -m "那历史消息谁维护？"
python3 main.py --demo --reset-between -m "A" -m "B"
```

有真实 Key 时（可选，勿提交 `.env`）：

```bash
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_MODEL=gpt-4o-mini
python3 main.py -m "用一句话自我介绍" -m "刚才你说你是谁？"
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] 首轮请求 messages 为 `[system, user]`
- [ ] 次轮请求包含上一轮 `user` + `assistant`
- [ ] `reset` 后历史清空，人设仍在
- [ ] 空 system / 空 user 抛出 `ValueError`
- [ ] `--demo` 可观察多轮 `history` 变长

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能画出两轮对话各自发出的 `messages` 数组
- [ ] 我知道为什么 API「不记得」上一句：因为无状态
- [ ] 我能说明 `history()` 为何要返回副本
- [ ] 我已知明天 Day 13：流式输出（SSE / chunk 打印）

---

## 通知摘要（便于推送）

**Day 12｜角色消息与多轮上下文**  
实现固定人设助手：`system` + 本地历史拼装多轮 `messages`；Mock 验证上下文回传。  
路径：`daily/2026-08-05/`
