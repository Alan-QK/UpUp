# Day 30｜周挑战：会议纪要结构化

> 日期：2026-09-02（周三）  
> Phase 2 / Week 6 · 学习日序号：**D30 / 120**  
> 建议时长：**90 分钟**（概念 20 + Coding 65 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 把 Week 6 的能力（Prompt 章节、JSON 抽取、pydantic、导出）**拼成一条可交付流水线**
2. 从非结构化会议纪要抽出 **决议（decisions）** 与 **行动项（action items）**
3. 校验嵌套 Schema（含日期规范化、优先级枚举），再渲染 Markdown / 导出 CSV
4. 说清：结构化纪要是「给人评审的摘要」+「给看板/表格的任务清单」两条交付物

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 6 · D30）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾：[`../2026-08-27/notes.md`](../2026-08-27/notes.md)、[`../2026-09-01/notes.md`](../2026-09-01/notes.md)

重点抓住三件事：

- **嵌套结构**：`MeetingMinutes` 内含 `ActionItem[]`，比扁平 Contact 更贴近真实 Agent 输出
- **双交付**：Markdown 给人扫；CSV 给任务跟进（负责人 / 截止日期）
- **周挑战心态**：不引入新框架，把已学积木拼成闭环

---

## Coding 练习（65 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest 'pydantic>=2'
```

### 任务

1. 完成 `exercise/meeting_minutes.py` 中标有 TODO 的函数（Schema 与 JSON 抽取辅助已给出，勿改）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-09-02/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py
python3 main.py --format csv
python3 main.py --show-prompt
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] 能组装带【角色/任务/约束/输出格式】的 system Prompt，并用边界标记包裹会议原文
- [ ] 能从围栏/前后废话中抽出 JSON，并校验为 `MeetingMinutes`
- [ ] `normalize_date` 能把常见日期写法规范成 `YYYY-MM-DD`
- [ ] 可渲染 Markdown；行动项可导出 CSV（含表头）
- [ ] 不要引入 langchain / openai SDK（今日用可注入的 `complete_fn` mock）

---

## 参考实现

先自己做。卡住超过 25 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能画出：纪要文本 → Prompt → LLM → JSON → pydantic → Markdown / CSV
- [ ] 我知道为什么 action item 要强制 `owner` + `task`（没有负责人的待办等于没有待办）
- [ ] 我能说出：决议偏「已拍板事实」，行动项偏「未来要做的事」——字段设计要分开
- [ ] 我清楚下周进入 RAG：文档加载与切分（先有干净文本，再谈检索）

---

## 本周收口（Week 6）

| Day | 能力 |
|-----|------|
| 26 | JSON + pydantic 校验 |
| 27 | 校验失败重试（repair loop） |
| 28 | 函数 → JSON Schema（工具预备） |
| 29 | 批量信息抽取 |
| **30** | **会议纪要结构化（周挑战）** |

下一周进入 **RAG 数据层**：文档加载、清洗与 Chunking。

---

## 通知摘要（便于推送）

**Day 30｜周挑战：会议纪要结构化**  
从会议原文抽出决议与 action items，pydantic 校验后导出 Markdown/CSV。  
路径：`daily/2026-09-02/`
