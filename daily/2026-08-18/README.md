# Day 20｜里程碑：cli-chatbot

> 日期：2026-08-18（周二）  
> Phase 1 / Week 4 · 学习日序号：**D20 / 120**  
> 建议时长：**90 分钟**（概念 15 + Coding 70 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 把 Phase 1 的能力收成一个可演示项目：`projects/cli-chatbot`
2. 在同一条链路上同时具备：**密钥来自环境**、**流式输出**、**多轮 + /reset /exit**、**历史滑动窗口**
3. 用 Mock 离线跑通 pytest（不依赖外网与真实 Key）
4. 对照阶段验收清单，写出一次「坏回复」复盘

---

## 学习内容（15 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（**里程碑验收清单**）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选速览：Day 13 流式 / Day 15 会话 / Day 16 窗口 / Day 9 密钥

重点抓住三件事：

- **里程碑 ≠ 新概念堆料**：今天是「拼装 + 打磨」
- **流式是传输形态，窗口是本地策略**：两者正交，合在一个 Assistant 里
- **作品要可演示**：`--demo` 必须能脚本化跑通

---

## Coding 练习（70 分钟）

目录：[`exercise/`](./exercise/)

### 任务

1. 完成 `exercise/streaming_assistant.py` 中的 TODO（`StreamingWindowedAssistant`）
2. 其余文件已给齐：`streaming_client` / `history_window` / `env_loader` / `chat_session` / `main`
3. 跑通测试：

```bash
cd daily/2026-08-18/exercise
python3 -m pip install --user httpx   # 若尚未安装
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo --line "用一句话解释 Agent" --line /history --line /reset --line "新会话" --line /exit
```

交互打字机效果（可选）：

```bash
python3 main.py --demo
```

5. **提交里程碑**：把可运行实现同步到 [`projects/cli-chatbot/`](../../projects/cli-chatbot/)（本仓库已提供完整参考副本；你自学时请先做 exercise，再对照 solution / projects）

### 验收标准（对齐 Phase 1）

- [ ] `pytest` 全部通过（≥ 3 个用例；今日练习已覆盖更多）
- [ ] 支持多轮对话与 `/reset`、`/exit`（另有 `/help` `/history`）
- [ ] 支持流式输出（`stream: true` + SSE delta；终端可打字机打印）
- [ ] API Key 仅从环境变量 / `.env` 读取（demo 模式除外）
- [ ] `projects/cli-chatbot/README.md` 能按文档安装运行
- [ ] 在 [`notes.md`](./notes.md)「坏回复复盘」写下一次观察

---

## 参考实现

先自己做。卡住超过 25 分钟再看：[`solution/`](./solution/)

打磨后的项目位置：[`projects/cli-chatbot/`](../../projects/cli-chatbot/)

---

## 自检清单

- [ ] 我能画出：env → client → assistant(window+stream) → session → CLI
- [ ] 我知道为什么错误发生时不应写入本轮 history
- [ ] 我能向同事 3 分钟讲清这个 CLI 的能力边界
- [ ] Phase 1 结束后，我清楚 Phase 2 将进入 Prompt / RAG

---

## 通知摘要（便于推送）

**Day 20｜里程碑：cli-chatbot**  
打磨命令行流式聊天机器人：环境变量密钥 + SSE 流式 + 滑动窗口 + /reset /exit；提交 `projects/cli-chatbot`。  
路径：`daily/2026-08-18/` · 项目：`projects/cli-chatbot/`
