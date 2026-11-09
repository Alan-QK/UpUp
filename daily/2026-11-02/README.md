# Day 64｜记忆写入策略

> 日期：2026-11-02（周一）  
> Phase 4 / Week 13 · 学习日序号：**D64 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清「能存」≠「该存」：长期记忆需要写入闸门
2. 用规则启发式实现 `write / skip / ask` 三态决策
3. 处理显式记住、偏好、事实、寒暄、敏感信息等信号
4. 把 WRITE 结果衔接到 Day 63 的向量记忆库（概念上）

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-04-memory-multiagent.md`](../../curriculum/phases/phase-04-memory-multiagent.md)（Week 13 · D64）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾：Day 63 长期向量记忆、Day 59 HITL 确认

重点抓住三件事：

- **默认不记**：一次性任务与寒暄应 SKIP
- **敏感绝不写**：密码 / API Key / 手机号直接 SKIP
- **犹豫就 ASK**：像偏好但不坚定时，交给人确认

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**调用 LLM；**不要**接真实数据库。

### 任务

1. 完成 `exercise/memory_policy.py` 中的 TODO  
   （归一化、敏感检测、决策流水线、批量统计、报告）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-11-02/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --report
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] `decide_write` 对非 user / 敏感 / 显式勿记正确 SKIP
- [ ] 显式请记与稳定偏好 → WRITE；带犹豫词的偏好 → ASK
- [ ] `filter_writable` 只保留 WRITE
- [ ] `render_memory_policy_report` 含规定二级标题
- [ ] 全程标准库

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能解释：为什么不能把每句用户话都写入向量库
- [ ] 我知道 WRITE / SKIP / ASK 各自交给谁处理（库 / 丢弃 / HITL）
- [ ] 我能说出至少 4 条写入启发式的优先级
- [ ] 我已知明天 Day 65：周挑战——带记忆助理（跨两次运行仍记得）

---

## 本周预告（Week 13 · 记忆系统）

| Day | 主题 |
|-----|------|
| 61 | 会话记忆回顾 / 增强窗口 |
| 62 | 摘要记忆 |
| 63 | 长期向量记忆 |
| **64** | **记忆写入策略（今天）** |
| 65 | 周挑战：带记忆助理 |

---

## 通知摘要（便于推送）

**Day 64｜记忆写入策略**  
用启发式决定何时写入长期记忆：write / skip / ask 三态闸门。  
路径：`daily/2026-11-02/`
