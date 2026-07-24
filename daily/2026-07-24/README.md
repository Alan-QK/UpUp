# Day 5｜周挑战：迷你 CLI 工具

> 日期：2026-07-24（周五）  
> Phase 1 / Week 1 · 学习日序号：**D5 / 120**  
> 建议时长：**90 分钟**（概念 20 + Coding 65 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 把本周学过的 dataclass / JSON / pathlib / pytest **拼成一个可运行小工具**
2. 用 `argparse` 做出「增 / 删 / 查」的命令行入口
3. 把业务逻辑（store）与 CLI（main）拆开，方便单测
4. 完成本周挑战：一份本地持久化的**笔记 CLI**

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 1 回顾）
2. 今日笔记：[`notes.md`](./notes.md)

重点抓住三件事：

- **CLI = 薄壳**：解析参数 → 调 store → 打印结果；别把 JSON 读写塞进 `main`
- **Store = 可测内核**：增删查都是纯文件 + 内存操作，必须有 pytest
- **本周收口**：环境、模型、IO、模块、测试 → 今天端到端串起来

---

## Coding 练习（65 分钟）

目录：[`exercise/`](./exercise/)

### 任务

实现一个本地笔记 CLI（JSON 持久化）：

1. 完成 `exercise/note_store.py` 中的 TODO（`Note` + `NoteStore`）
2. 阅读并可选微调 `exercise/main.py`（argparse 入口已搭好）
3. 跑通测试：

```bash
cd daily/2026-07-24/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py add "Agent 想法" "先拆工具函数再接 LLM"
python3 main.py list
python3 main.py get 1
python3 main.py search "工具"
python3 main.py delete 1
python3 main.py list
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] 支持 `add` / `list` / `get` / `delete` / `search`
- [ ] 数据落在 JSON 文件（默认 `notes.json`），重启 CLI 后仍在
- [ ] 查不到 id 时抛出 `NoteNotFoundError`（CLI 打印友好错误）
- [ ] 你能用一句话说明：为什么 store 与 CLI 要拆开

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能解释 `argparse` 子命令（subparsers）在干什么
- [ ] 我知道为什么测试要用 `tmp_path`，而不是写死仓库里的 `notes.json`
- [ ] 本周 5 天知识点我能串成一条线（见笔记末尾）
- [ ] 我已知下周 Day 6：HTTP 与 httpx

---

## 通知摘要（便于推送）

**Day 5｜周挑战：迷你 CLI 工具**  
实现本地笔记 CLI（增删查 + JSON 持久化），跑通 pytest 与手工命令。  
路径：`daily/2026-07-24/`
