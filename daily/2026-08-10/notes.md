# Day 15 笔记｜周挑战：多轮对话 CLI

## 1. 今天为什么是「周挑战」？

Week 3 把「能调模型」升级成「能聊得下去」：

| Day | 能力 | 今天用在哪 |
|-----|------|-----------|
| D11 | Chat Completions | 真正发请求 |
| D12 | system / 历史拼装 | `PersonaAssistant` |
| D13 | 流式直觉 | 明日里程碑会接；今天先稳住会话循环 |
| D14 | token / 成本 | 多轮会让 prompt 变贵——心里有数 |
| D15 | **会话 CLI** | `/reset` `/exit` + REPL |

前端类比：你已经会写 `fetch` 调聊天接口、会维护 messages 数组；今天补的是**聊天窗的输入循环与命令协议**。

## 2. 架构：薄 CLI + 厚 Session

```text
用户敲一行
    ↓
main.py（REPL / --line / --demo）
    ↓
ChatSession.handle_line   ← 今天你要写的
    ↓
  斜杠命令？─── /reset /exit /help /history
    │
    └─ 普通文本 → PersonaAssistant.ask → ChatClient.complete
```

**好习惯**：

- Session 不知道怎么 `input()` / 上色打印
- CLI 不知道 messages 怎么拼
- 测试只打 Session（Mock 掉 HTTP）

以后做前端对话页：Session ≈ hooks 里的会话状态机；CLI ≈ 一个极简 UI。

## 3. 斜杠命令：给「人机协议」留口子

纯聊天框很快不够用。Agent 产品常见：

| 命令 | 含义 | Agent 侧对应 |
|------|------|--------------|
| `/reset` | 开新会话 | 清短期记忆，保留人设 |
| `/exit` | 结束 | 关连接 / 停 worker |
| `/help` | 能力说明 | 工具列表 / 使用说明 |
| `/history` | 看上下文 | Debug 面板 |

约定：

- 命令以 `/` 开头，**大小写不敏感**
- 只解析第一个 token（`/reset now` 仍当 `/reset`）
- 未知命令要友好提示，别当普通 chat 发给模型（否则模型可能一本正经「执行」幻觉命令）

## 4. 空输入与错误：会话层要兜住

REPL 里用户会：

- 狂按回车 → 空输入应忽略，别发空 `user`
- 网络 500 / 超时 → **不要把整个 CLI 打崩**；转成可读 system 提示

今天练习要求捕获 `ChatClientError`，返回：

```text
调用失败：HTTP 500: ...
```

Agent 同理：工具失败应变成「观察」，而不是进程退出。

## 5. `/history` 与截断

调试时你要能快速扫上下文。格式建议：

```text
当前历史共 2 条消息：
[user] 你好
[assistant] [demo·第1轮] 你好
```

内容过长时截断到 80 字符 + `...`，避免刷屏。  
注意：这里的 history **不含 system**（人设在 PersonaAssistant 内部，不进 history 列表）。

## 6. `--demo` 与 `--line`：可测、可脚本化

| 模式 | 用途 |
|------|------|
| 交互 `input()` | 人手感体验 |
| `--line a --line b --line /exit` | 脚本化验收、CI 友好 |
| `--demo` | MockTransport，无 Key / 无外网 |

学习阶段优先保证 **离线路径永远绿**；真调 API 是加分项。

## 7. 本周知识点串线

```text
协议字段（D11）
  → 角色与本地历史（D12）
  → 流式体验（D13）
  → 用量与成本（D14）
  → 会话循环与命令（D15）
```

下一周（Day 16 起）会在这个 CLI 骨架上加：**历史裁剪、采样参数、Provider 抽象、结构化日志**，并在 Day 20 收成里程碑 `cli-chatbot`。

## 8. 前端迁移一问

如果把今天的 Session 接到 Web：

- `/reset` → 「新对话」按钮
- `should_exit` → 关闭抽屉 / 停生成
- `kind=system` → 灰色提示条；`kind=assistant` → 气泡
- 捕获的 `ChatClientError` → Toast，而不是白屏
