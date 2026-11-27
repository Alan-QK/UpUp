# Day 65｜周挑战：带记忆助理

> 日期：2026-11-03（周二）  
> Phase 4 / Week 13 · 学习日序号：**D65 / 120**  
> 建议时长：**90 分钟**（复盘 20 + Coding 60 + 自检 10）

---

## 今日目标

学完今天，你能够：

1. 把本周四块能力拼成一条链路：闸门 → 向量库 → 持久化 → 召回注入
2. 用 JSON 文件实现**跨两次运行**仍记得用户偏好
3. 用新 `MemoryAssistant` 实例证明「记得」来自磁盘，而不是进程内缓存
4. 说清短记忆 / 摘要 / 长期记忆各自解决什么问题

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-04-memory-multiagent.md`](../../curriculum/phases/phase-04-memory-multiagent.md)（Week 13 · D65）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾：Day 61–64 的 `solution/`

重点抓住三件事：

- **跨会话 ≠ 更长的 context window**：窗口再大也会清空；长期记忆要落盘
- **先闸门再写入**：寒暄、敏感、一次性任务不应进长期库
- **召回是按需注入**：第二次运行按当前问题检索，不是把全部记忆塞进 prompt

---

## Coding 练习（60 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**调用 LLM；**不要**接真实向量数据库。

### 任务

1. 完成 `exercise/memory_assistant.py` 中的 TODO  
   （`FileMemoryStore`、`MemoryAssistant`、跨运行 demo、报告）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-11-03/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --report
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] 同一 `store_path` 下，第二次 `MemoryAssistant` 能召回第一次写入的偏好
- [ ] 寒暄 / 敏感 / 无信号 → 不写库；显式记住 / 稳定偏好 / 事实 → 写库
- [ ] ASK 需 `confirm_fn` 同意才写入
- [ ] 不同 `user_id` 记忆隔离
- [ ] `render_memory_assistant_report` 含规定二级标题
- [ ] 全程标准库

---

## 参考实现

先自己做。卡住超过 25 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能解释：为什么「把 messages 列表存全局」不算跨运行记忆
- [ ] 我能画出：用户话 → decide_write → upsert → JSON → 下次 load → search → 回复
- [ ] 我知道 ASK 与 WRITE 的产品差异（HITL vs 自动落库）
- [ ] 我已知下周 Day 66：任务分解 Planner

---

## 本周回顾（Week 13 · 记忆系统）

| Day | 主题 |
|-----|------|
| 61 | 会话记忆回顾 / 增强窗口 |
| 62 | 摘要记忆 |
| 63 | 长期向量记忆 |
| 64 | 记忆写入策略 |
| **65** | **周挑战：带记忆助理（今天）** |

---

## 通知摘要（便于推送）

**Day 65｜周挑战：带记忆助理**  
拼装本周记忆能力：JSON 持久化 + 写入闸门，跨两次运行仍记得偏好。  
路径：`daily/2026-11-03/`
