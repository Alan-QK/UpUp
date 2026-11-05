# Day 29｜批量信息抽取

> 日期：2026-09-01（周二）  
> Phase 2 / Week 6 · 学习日序号：**D29 / 120**  
> 建议时长：**80 分钟**（概念 25 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清「单条结构化抽取」和「批量抽取流水线」的差别（隔离失败、汇总、导出）
2. 用 pydantic 校验每条抽取结果，失败记入结果而不中断整批
3. 把成功记录导出为 **JSON** 与 **CSV**（Agent 落地常见交付物）
4. 用 mock LLM 跑通「文本列表 → 字段表」闭环（不烧真实 API）

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 6 · D29）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾：[`../2026-08-27/notes.md`](../2026-08-27/notes.md)（JSON + pydantic）、[`../2026-08-28/notes.md`](../2026-08-28/notes.md)（单条 repair）

重点抓住三件事：

- **批处理 ≠ for 循环调 API**：要有 source_id、成功/失败隔离、摘要统计
- **导出是产品边界**：JSON 给程序，CSV 给人 / 表格工具
- **前端类比**：CRM「粘贴名片文字 → 导入联系人」；今天做后端那一段

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest 'pydantic>=2'
```

### 任务

1. 完成 `exercise/batch_extract.py` 中标有 TODO 的函数（`Contact` Schema 与 JSON 抽取辅助已给出，勿改）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-09-01/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py
python3 main.py --format csv
python3 main.py --fail-one
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `extract_one` / `extract_batch`：单条失败不影响其他条
- [ ] `contacts_to_csv` 带表头、正确转义逗号/引号
- [ ] `batch_summary` 给出 total / ok / failed
- [ ] 不要引入 langchain / openai SDK（今日用可注入的 `complete_fn` mock）

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能画出：文本 → Prompt → LLM → JSON → pydantic → 成功列表 / 失败列表 → CSV/JSON
- [ ] 我知道为什么每条记录要带 `source_id`（对账、重跑、前端定位）
- [ ] 我能说出：Day 27 的 repair 适合「贵且关键的单条」；批量流水线通常先记失败再抽重跑
- [ ] 我知道明天周五挑战是：会议纪要 → 决议 + action items

---

## 本周地图（Week 6）

| Day | 主题 |
|-----|------|
| 26 | JSON + pydantic 校验 |
| 27 | 校验失败重试（repair loop） |
| 28 | 函数 → JSON Schema（工具预备） |
| **29** | **批量信息抽取** ← 今天 |
| 30 | 周挑战：会议纪要结构化 |

---

## 通知摘要（便于推送）

**Day 29｜批量信息抽取**  
从多段非结构化文本批抽取联系人字段，校验后导出 JSON/CSV；单条失败不拖垮整批。  
路径：`daily/2026-09-01/`
