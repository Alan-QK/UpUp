# Day 25｜周挑战：用户故事生成器

> 日期：2026-08-26（周三）  
> Phase 2 / Week 5 · 学习日序号：**D25 / 120**  
> 建议时长：**90 分钟**（概念 20 + Coding 65 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 把 Week 5 的 Prompt 积木（结构 / few-shot / 边界包裹）**拼成一条可交付流水线**
2. 规定模型只输出 **JSON 用户故事**，并能从「带废话的回复」里稳健抽出对象
3. 校验字段（角色句式、验收标准、优先级），再渲染成 Markdown 给人评审
4. 说清：今天的校验是「手写规则」；下周（Day 26）会升级到 schema / pydantic

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 5 · D25）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选回顾：Day 21 章节拼装、Day 22 few-shot、Day 24 输入包裹

重点抓住三件事：

- **模板化生成**：同一 system，只换 requirement，输出形状不变
- **JSON 是契约**：先约定字段，再让模型填空；解析失败要能定位
- **人机评审环**：Markdown 给人看，JSON 给程序看——两条输出都要有

---

## Coding 练习（65 分钟）

目录：[`exercise/`](./exercise/)

### 任务

1. 完成 `exercise/user_story.py` 中的 TODO
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-08-26/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --demo --show-prompt
python3 main.py --demo --json
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] 能组装带【角色/任务/约束/输出格式/示例】的 system Prompt
- [ ] 需求文本被 `<<<REQUIREMENT>>>` 包裹
- [ ] 能从围栏/前后废话中抽出 JSON 并解析为 `UserStory`
- [ ] `priority` 仅允许 `must|should|could`；`acceptance_criteria` 至少 1 条
- [ ] 可渲染 Markdown；`stories_to_dict` 可再 JSON 序列化
- [ ] 全程标准库（不要引入 langchain / openai / pydantic）

---

## 参考实现

先自己做。卡住超过 25 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能向同事讲清：为什么「先定 JSON 形状」比「先让模型自由发挥」更稳
- [ ] 我知道 few-shot 放在 system 里是为了锁定输出风格，而不是堆砌业务知识
- [ ] 我能指出：解析失败时，是 Prompt 问题、模型跑偏，还是抽取代码太脆
- [ ] 我清楚下周会用更强的 schema 校验接上今天的流水线
- [ ] （可选）用自己的一句产品需求改 `--requirement`，对照 mock 思考真实接入时怎么换

---

## 本周收口（Week 5）

| Day | 能力 |
|-----|------|
| 21 | Prompt 组件化 |
| 22 | Few-shot / 反例 |
| 23 | CoT vs 直接答 |
| 24 | 注入边界 |
| **25** | **模板化生成 + JSON 契约（周挑战）** |

下一周进入 **结构化输出**：pydantic 校验与 repair loop。
