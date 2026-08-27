# Day 21｜Prompt 结构拆解

> 日期：2026-08-20（周四）  
> Phase 2 / Week 5 · 学习日序号：**D21 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 把「玄学 Prompt」拆成固定四件套：**角色 / 任务 / 约束 / 输出格式**（可选再加上下文）
2. 用 Python 搭一个可复用的 Prompt 模板函数库（纯标准库）
3. 把模板渲染成 OpenAI 风格的 `messages`（system + user）
4. 说清：为什么结构化 Prompt 比「一长串散文」更稳、更好测、更好迭代

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 5 开篇）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾：Day 12 的 system / user 角色分工——今天把 **system 内容本身**结构化

重点抓住三件事：

- **角色**：模型「扮演谁 / 站在什么立场」
- **任务**：这一轮「具体要交付什么」
- **约束 + 格式**：边界在哪、输出长什么样（可校验的前提）

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 任务

1. 完成 `exercise/prompt_builder.py` 中的 TODO
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-08-20/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --demo --task "把这段话改写成三条要点"
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `PromptSpec` 能表达角色 / 任务 / 约束 / 输出格式 / 可选上下文
- [ ] `render_system_prompt` 按固定章节顺序拼装，空章节可省略
- [ ] `build_chat_messages` 返回 `[{role:system},{role:user}]`
- [ ] 空角色 / 空任务 / 空输出格式会 `ValueError`
- [ ] 全程标准库（不要引入 jinja2 / langchain）

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能用一句话解释四件套各自解决什么问题
- [ ] 我知道 system 适合放「稳定规则」，user 适合放「本轮输入」
- [ ] 我不会再把约束、格式、示例全揉成一段无法 diff 的超长字符串
- [ ] 我已知明天 Day 22：Few-shot 与反例（在模板里挂示例）
