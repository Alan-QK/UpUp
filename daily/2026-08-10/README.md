# Day 15｜周挑战：多轮对话 CLI

> 日期：2026-08-10（周一）  
> Phase 1 / Week 3 · 学习日序号：**D15 / 120**  
> 建议时长：**90 分钟**（概念 20 + Coding 65 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 把本周学过的 **Chat Completions / 角色历史 / 错误处理** 拼成一个可运行聊天 CLI
2. 实现会话循环：普通输入走模型，斜杠命令走本地协议
3. 支持 `/reset`、`/exit`（及 `/help`、`/history`）
4. 用 Mock 离线跑通 pytest 与脚本化 Demo（不依赖外网与真实 Key）

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 3 回顾）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾 Day 12：[`daily/2026-08-05/notes.md`](../2026-08-05/notes.md)

重点抓住三件事：

- **CLI 薄、Session 厚**：命令解析与状态机要可单测
- **`/reset` ≠ 换人设**：只清历史，system 仍在
- **本周收口**：能调模型 → 能多轮 → 能在终端里稳定聊

---

## Coding 练习（65 分钟）

目录：[`exercise/`](./exercise/)

### 任务

实现带斜杠命令的多轮对话会话层，并跑通 CLI。

1. 完成 `exercise/chat_session.py` 中的 TODO
2. `chat_client.py` / `persona_assistant.py` **已给齐**，无需改
3. 阅读 `exercise/main.py`（REPL 与 `--line` 已搭好）
4. 跑通测试：

```bash
cd daily/2026-08-10/exercise
python3 -m pytest -q
```

若尚未安装 httpx：

```bash
python3 -m pip install --user httpx
```

5. 手工试跑（离线 Demo）：

```bash
python3 main.py --demo --line "用一句话解释 messages" --line /history --line /reset --line "新会话你好" --line /exit
```

交互模式（可选）：

```bash
python3 main.py --demo
# 然后依次输入聊天内容、/help、/reset、/exit
```

有真实 Key 时（可选，勿提交 `.env`）：

```bash
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_MODEL=gpt-4o-mini
python3 main.py --line "你好" --line "还记得我是谁吗？" --line /exit
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] 支持 `/help` `/reset` `/history` `/exit`（`/quit` 同义）
- [ ] 普通文本走多轮聊天；第二轮请求带上第一轮历史
- [ ] `/reset` 后历史清空，人设仍在
- [ ] 空输入忽略；`ChatClientError` 转为 system 提示而不崩溃
- [ ] `--demo` + `--line` 可脚本化验收

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能画出「用户输入一行」后 Session 的分支（命令 vs 聊天）
- [ ] 我知道为什么要把命令解析从 `main.py` 拆出去
- [ ] 本周 5 天知识点我能串成一条线（见笔记末尾）
- [ ] 我已知明天 Day 16：历史消息裁剪（滑动窗口）

---

## 通知摘要（便于推送）

**Day 15｜周挑战：多轮对话 CLI**  
实现带 `/reset` `/exit` 的会话循环：Session 层可单测，CLI 支持 `--demo` 离线脚本验收。  
路径：`daily/2026-08-10/`
