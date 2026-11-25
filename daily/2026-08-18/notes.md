# Day 20 笔记｜里程碑：cli-chatbot

## 1. 今天学什么？

Phase 1 收官：不学新框架，把四周积木拼成**可演示作品**。

| 积木 | 来自 | 在里程碑里的角色 |
|------|------|------------------|
| `.env` / `require_env` / 脱敏 | Day 9 | 启动配置，Key 不进代码 |
| Chat Completions + SSE | Day 11/13 | 真正的模型 I/O |
| 斜杠命令会话 | Day 15 | `/reset` `/exit` `/help` `/history` |
| 滑动窗口 | Day 16 | 控制上下文长度与成本 |
| 结构化日志意识 | Day 19 | （本里程碑可选增强；先保证主路径） |

前端类比：今天像把分散的 hooks/utils 收成一个可上线的「最小 App」——路由（命令）、状态（history）、请求层（client）、UI（终端流式打印）。

## 2. 核心对象怎么分层？

```text
main.py (CLI / --demo / --line)
  └─ ChatSession          # 命令协议，可单测
       └─ StreamingWindowedAssistant
            ├─ sliding_window(...)   # 本地策略
            └─ StreamingChatClient   # 网络 + SSE
```

原则：

1. **Session 不关心 SSE 细节**——它只认 `ask/reset/history`
2. **Assistant 负责「何时裁历史、何时写入历史」**
3. **Client 只负责协议**——`stream: true`、解析 delta

## 3. 流式 + 窗口的两个易错点

1. **必须消费完迭代器再写入历史**  
   若中途异常，本轮 user/assistant **都不要**进 history（否则会出现「只有问没有答」的脏状态）。

2. **请求前裁，还是写入后再裁？**  
   与 Day 16 一致：请求时用 `sliding_window(history)` 构造 messages；追加本轮后，再 `history = sliding_window(history)`，保证本地存储也不膨胀。

## 4. 演示与真调

| 模式 | 怎么用 |
|------|--------|
| Demo | `python3 main.py --demo --line ...`，MockTransport，零费用 |
| Live | 配置 `OPENAI_API_KEY`（可用 `sample.env`），不要提交真实 `.env` |

## 5. 坏回复复盘（请自己填写）

> 阶段验收要求：记录一次「坏回复」并分析原因。

1. **现象**（模型说了什么／哪一步不对）：  
2. **可能原因**（人设？温度？上下文被裁掉？Prompt 含糊？）：  
3. **我会怎么改**（改 system / 改窗口 / 加约束 / 加示例）：  

（若暂时没跑真模型：用 `--demo` 观察「第 N 轮」回声，写清你对多轮上下文的预期与实测。）

## 6. 今日一句话

> 里程碑的价值不是代码行数，而是：别人按 README 能跑起来，你能讲清每一层为什么存在。

## 7. 明日预告

Day 21 起进入 **Phase 2**：Prompt 结构拆解——开始认真对待「怎么问模型」。

---

## 我的记录（请自己填写）

1.  
2.  
3.  
