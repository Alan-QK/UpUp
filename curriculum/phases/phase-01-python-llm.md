# Phase 1｜Python 强化 + LLM API 基础

> 周期：Week 1–4（约 20 个工作日）  
> 关键词：Python 工程习惯、异步、HTTP、Chat Completions、流式输出

---

## 阶段目标

学完本阶段，你应该能够：

1. 用类型注解写出可读的 Python 小模块
2. 管理虚拟环境与依赖，正确使用 `.env`
3. 调用 OpenAI 兼容 Chat API（同步 + 流式）
4. 理解 token、温度、上下文窗口的基本含义
5. 交付里程碑：命令行流式聊天机器人 `projects/cli-chatbot`

---

## 周计划

### Week 1 · Python 基本功回炉

| Day | 主题 | Coding |
|-----|------|--------|
| D1 | 环境、uv/poetry、项目结构、类型注解 | Hello + 类型练习 |
| D2 | 函数、dataclass、Enum、异常设计 | 小工具模块 |
| D3 | 文件 I/O、JSON、pathlib | 读写配置与日志 |
| D4 | 模块与包、测试入门 pytest | 给工具写测试 |
| D5 | 周挑战：CLI 待办/笔记工具 | 完整小 CLI |

### Week 2 · 网络与异步

| Day | 主题 | Coding |
|-----|------|--------|
| D6 | HTTP 基础与 httpx | GET/POST JSON |
| D7 | 错误处理、超时、重试 | 可重试客户端 |
| D8 | asyncio 基础 | 并发请求 Demo |
| D9 | 环境变量与密钥安全 | `.env` 加载器 |
| D10 | 周挑战：天气/笑话聚合 CLI | 多 API 聚合 |

### Week 3 · LLM API 入门

| Day | 主题 | Coding |
|-----|------|--------|
| D11 | Chat Completions 协议 | 第一次对话 |
| D12 | system/user/assistant 角色 | 角色化助手 |
| D13 | 流式输出（SSE） | 流式打印 |
| D14 | token 与成本估算 | 简单计费日志 |
| D15 | 周挑战：多轮对话 CLI（内存中） | 会话循环 |

### Week 4 · 巩固与里程碑

| Day | 主题 | Coding |
|-----|------|--------|
| D16 | 消息历史裁剪策略 | 滑动窗口 |
| D17 | 参数：temperature / top_p | 对比实验 |
| D18 | 模型抽象层（便于换厂商） | Provider 接口 |
| D19 | 日志与调试技巧 | 结构化日志 |
| D20 | 里程碑验收：`cli-chatbot` | 项目打磨 |

---

## 里程碑验收清单

- [ ] `README` 说明如何安装与运行
- [ ] 支持多轮对话与 `/reset`、`/exit`
- [ ] 支持流式输出
- [ ] API Key 仅从环境变量读取
- [ ] 至少 3 个 pytest 用例（可用 mock）
- [ ] 记录一次「坏回复」并分析原因（写在 notes）

---

## 推荐资源

- Python 官方 Tutorial（按需查）
- OpenAI API Reference（Chat Completions）
- httpx 文档
- Real Python：asyncio 入门文（任选一篇）

## 完成后进入

→ [Phase 2：Prompt / 结构化输出 / RAG](./phase-02-prompt-rag.md)
