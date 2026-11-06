# Day 63｜长期向量记忆

> 日期：2026-10-29（周四）  
> Phase 4 / Week 13 · 学习日序号：**D63 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清短期窗口、摘要记忆、长期向量记忆三者的边界
2. 用确定性 `mock_embed` + 余弦相似度实现进程内向量记忆库
3. 按 `user_id` 隔离存储/检索用户偏好，并格式化注入块
4. 理解：真 Embedding / 真向量库只是换「底座」，产品接口可以先定

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-04-memory-multiagent.md`](../../curriculum/phases/phase-04-memory-multiagent.md)（Week 13 · D63）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾：Day 33 Embedding、Day 34 向量库、Day 62 摘要记忆

重点抓住三件事：

- **长期记忆 = 跨会话 + 按需召回**，不是每轮全量塞上下文
- **先按用户隔离，再算相似度**
- **embed 可插拔**：练习用 mock，生产换真 API

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / chromadb / langchain；**不要**调用真实 Embedding API。

### 任务

1. 完成 `exercise/vector_memory.py` 中的 TODO  
   （mock embedding、余弦相似度、Store CRUD、语义检索、报告）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-10-29/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --cross
python3 main.py --report
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] `mock_embed` 维度固定为 32，非空文本 L2 范数约为 1
- [ ] 同一 `memory_id` upsert 会覆盖；`user_id` 检索互不串扰
- [ ] `search` 支持 `top_k` / `min_score`；命中可格式化为 `[长期记忆]` 块
- [ ] `render_vector_memory_report` 含规定二级标题
- [ ] 全程标准库

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能解释：为什么长期记忆不能替代短窗口与摘要
- [ ] 我知道 mock embed 与真 Embedding API 的接口应保持一致
- [ ] 我能说明：用户隔离为什么必须在相似度计算之前
- [ ] 我已知明天 Day 64：记忆写入策略（何时记）

---

## 本周预告（Week 13 · 记忆系统）

| Day | 主题 |
|-----|------|
| 61 | 会话记忆回顾 / 增强窗口 |
| 62 | 摘要记忆 |
| **63** | **长期向量记忆（今天）** |
| 64 | 记忆写入策略 |
| 65 | 周挑战：带记忆助理 |

---

## 通知摘要（便于推送）

**Day 63｜长期向量记忆**  
跨会话存储/检索用户偏好：mock embed + 余弦召回 + 用户隔离注入块。  
路径：`daily/2026-10-29/`
