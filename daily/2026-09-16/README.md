# Day 40｜里程碑：mini-rag

> 日期：2026-09-16（周三）  
> Phase 2 / Week 8 · 学习日序号：**D40 / 120**  
> 建议时长：**90 分钟**（概念 15 + Coding 70 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 把 Phase 2 的能力收成一个可演示项目：`projects/mini-rag`
2. 在同一条链路上同时具备：**可配置切分**、**检索问答**、**引用溯源**、**低相关拒答**、**golden set 评测**
3. 用假向量离线跑通 pytest（不依赖外网与真实 Embedding / Chat Key）
4. 对照阶段验收清单，写出一次「坏回答 / 误拒答」复盘

---

## 学习内容（15 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（**里程碑验收清单**）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选速览：Day 32 切分 / Day 36 链路 / Day 37 引用 / Day 38 拒答 / Day 39 评测

重点抓住三件事：

- **里程碑 ≠ 新概念堆料**：今天是「拼装 + 打磨」
- **编排层要薄**：`MiniRag` 只负责串联，不重写向量库或 Prompt 细节
- **作品要可演示**：`python3 main.py demo` 与 `eval` 必须脚本化跑通

---

## Coding 练习（70 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain / chromadb。

### 任务

1. 完成 `exercise/mini_rag.py` 中的 TODO（`MiniRag` 编排层）
2. 其余文件已给齐：`chunker` / `vector_store` / `rag_pipeline` / `citations` / `refusal` / `rag_eval` / `main`
3. 跑通测试：

```bash
cd daily/2026-09-16/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py demo
python3 main.py ask "RAG 为什么能降低幻觉"
python3 main.py ask "今天天气怎么样"
python3 main.py eval
```

5. **提交里程碑**：把可运行实现同步到 [`projects/mini-rag/`](../../projects/mini-rag/)（本仓库已提供完整参考副本；你自学时请先做 exercise，再对照 solution / projects）

### 验收标准（对齐 Phase 2）

- [ ] 支持 md/txt 文档加载
- [ ] 可配置 `chunk_size` / `overlap`
- [ ] 问答返回答案 + 引用来源（`display` 含「来源：」）
- [ ] 无相关上下文时能拒答
- [ ] README 含架构示意（见 `projects/mini-rag/README.md`）
- [ ] 准备 ≥5 条问答样例（本课 golden set 为 8 条）且 `pass_rate == 1.0`
- [ ] `pytest` 全部通过（纯本地）
- [ ] 在 [`notes.md`](./notes.md)「坏回答复盘」写下一次观察

---

## 参考实现

先自己做。卡住超过 25 分钟再看：[`solution/`](./solution/)

打磨后的项目位置：[`projects/mini-rag/`](../../projects/mini-rag/)

---

## 自检清单

- [ ] 我能画出：docs → chunk → embed → store → retrieve → gate → generate → cite
- [ ] 我知道为什么默认 `citation_mode=all` 对里程碑演示更稳
- [ ] 我能向同事 3 分钟讲清这个 mini-rag 的能力边界（假向量 / 无真模型）
- [ ] Phase 2 结束后，我清楚 Phase 3 将进入 Tool Calling / Agent Loop

---

## 通知摘要（便于推送）

**Day 40｜里程碑：mini-rag**  
打磨最小 RAG：可配置切分 + 检索问答 + 引用 + 拒答 + golden 评测；提交 `projects/mini-rag`。  
路径：`daily/2026-09-16/` · 项目：`projects/mini-rag/`
