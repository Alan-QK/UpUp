# Day 22｜Few-shot 与反例

> 日期：2026-08-21（周五）  
> Phase 2 / Week 5 · 学习日序号：**D22 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 解释 **zero-shot / one-shot / few-shot** 的差别，以及何时值得加示例
2. 在 Prompt 里同时挂 **正例** 与 **反例**（告诉模型「别把这种也标成 X」）
3. 用 Python 把文本分类任务渲染成可复用的 few-shot messages（纯标准库）
4. 说清：示例质量 > 示例数量；反例用来划清边界，不是堆噪声

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 5 · D22）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾：Day 21 的 Prompt 四件套——今天在「任务 / 格式」之外，专门加一节 **示例**

重点抓住三件事：

- **Few-shot**：用少量「输入 → 标签」示范，把隐式规则外显
- **反例**：展示「看起来像 A、其实是 B」的易混样本，降低误分类
- **可控输出**：分类任务优先「只吐标签」，方便后续校验（Day 26 会接 schema）

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 任务

1. 完成 `exercise/few_shot.py` 中的 TODO
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-08-21/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --demo --text "登录按钮点了没反应"
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `ShotExample` 能表达文本、标签、`kind`（`positive` / `counter`）
- [ ] 正例与反例分节渲染；空节可省略
- [ ] `build_classification_messages` 返回 `[{role:system},{role:user}]`
- [ ] 非法标签 / 空文本 / 非法 kind 会 `ValueError`
- [ ] 全程标准库（不要引入 langchain / openai SDK）

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能用一句话区分 zero-shot 与 few-shot
- [ ] 我知道反例解决的是「边界混淆」，不是「多贴几条正例」
- [ ] 我不会把示例写成散文故事，而是「输入 → 标签」的可复制格式
- [ ] 我已知下周 Day 23：思维链 vs 直接答案（对比实验）
