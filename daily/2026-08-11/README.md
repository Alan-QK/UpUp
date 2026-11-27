# Day 16｜历史消息裁剪（滑动窗口）

> 日期：2026-08-11（周二）  
> Phase 1 / Week 4 · 学习日序号：**D16 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 解释为什么多轮对话必须管理**上下文窗口**（成本 + 硬上限）
2. 实现按「轮」截取的 **滑动窗口**（保留最近 N 轮 user/assistant）
3. 做出 `WindowedAssistant`：人设常驻，请求与本地历史同步裁剪
4. 用 Mock 离线验证「旧轮从请求里消失」

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 4）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾 Day 12 / Day 14：多轮拼装与 token 成本

重点抓住三件事：

- **system 不进窗口数组**：人设单独拼在最前
- **按完整轮裁**，避免窗口以落单 assistant 开头
- 滑动窗口是遗忘换稳定；更聪明的记忆以后再学

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 任务

1. 完成 `exercise/history_window.py` 中的 TODO
2. `chat_client.py` **已给齐**，无需改
3. 阅读 `exercise/main.py`（`--demo` / `--max-turns` 已搭好）
4. 跑通测试：

```bash
cd daily/2026-08-11/exercise
python3 -m pytest -q
```

若尚未安装 httpx：

```bash
python3 -m pip install --user httpx
```

5. 手工试跑（离线 Demo）：

```bash
python3 main.py --demo --max-turns 2
python3 main.py --demo --max-turns 1 -m "我叫小前端" -m "我在学 Agent" -m "我叫什么？"
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `sliding_window` 只保留最近 `max_turns` 个完整轮
- [ ] `WindowedAssistant` 第 N 轮请求不再携带窗口外的旧 user/assistant
- [ ] 追加历史后本地 `history()` 长度也被窗口限制
- [ ] `system` 始终在请求第一条；空 prompt / 空 user / `max_turns<1` 抛 `ValueError`
- [ ] `--demo` 可观察不同 `max_turns` 下「记得」内容变化

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能用前端「列表只保留最近 N 条」类比滑动窗口
- [ ] 我知道上下文窗口撞上限时常见症状（报错 / 静默截断 / 变贵）
- [ ] 我能说出滑动窗口 vs 摘要压缩的取舍
- [ ] 我已知明天 Day 17：采样参数（temperature 等）对比实验

---

## 通知摘要（便于推送）

**Day 16｜历史消息裁剪（滑动窗口）**  
实现按轮截取的上下文窗口：人设常驻，只把最近 N 轮发给模型，并同步限制本地历史。  
路径：`daily/2026-08-11/`
