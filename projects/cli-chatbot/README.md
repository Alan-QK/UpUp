# cli-chatbot · Phase 1 里程碑

命令行流式聊天机器人：OpenAI 兼容 API + SSE 流式 + 多轮会话 + 滑动窗口 + 环境变量密钥。

## 能力

- 多轮对话，斜杠命令：`/help` `/reset` `/history` `/exit`（`/quit`）
- 流式输出（SSE）；交互模式终端打字机效果
- API Key 仅从环境变量读取（支持加载 `.env` / `sample.env`）
- `--demo` 离线 Mock，零费用可演示
- pytest 覆盖核心路径（MockTransport）

## 安装

```bash
cd projects/cli-chatbot
python3 -m pip install --user -r requirements.txt
```

## 运行

离线 Demo（推荐先跑）：

```bash
python3 main.py --demo --line "用一句话解释什么是 Agent" --line /history --line /exit
```

交互：

```bash
python3 main.py --demo
```

真调（勿提交真实 `.env`）：

```bash
cp sample.env .env   # 编辑填入 OPENAI_API_KEY
export $(grep -v '^#' .env | xargs)   # 或依赖程序 load_dotenv(sample.env)
python3 main.py --line "你好" --line /exit
```

## 测试

```bash
python3 -m pytest -q
```

## 模块结构

| 文件 | 职责 |
|------|------|
| `streaming_client.py` | OpenAI 兼容流式客户端 |
| `history_window.py` | 滑动窗口裁剪 |
| `streaming_assistant.py` | 人设 + 流式 + 窗口 |
| `chat_session.py` | 斜杠命令会话层 |
| `env_loader.py` | `.env` 与密钥读取 |
| `main.py` | CLI 入口 |

## 学习来源

对应课程 Day 20：`daily/2026-08-18/`
