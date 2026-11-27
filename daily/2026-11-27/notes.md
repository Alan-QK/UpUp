# Day 72 笔记｜流水线双 Agent：Research → Write

## 1. 一句话定位

**流水线多智能体**：角色串行、产物交接——A 的输出是 B 的唯一输入；边界靠合约，不靠「两个聊天机器人你一句我一句」。

## 2. 为什么先学流水线？

Day 71 说：有 `handoff_chain` + `distinct_roles` 才值得拆。流水线是最简单、最常见的拆法：

```text
Researcher（搜/摘）──ResearchBrief──► Writer（组织/成稿）──► Article
```

对比其他拓扑（明天以后才做）：

| 拓扑 | 形态 | 难度 |
|------|------|------|
| 流水线 | A → B → C | 低（今天） |
| 主管-工人 | Supervisor 路由到工人 | 中（Day 73） |
| 黑板/总线 | 多角色读写共享状态 | 中高（Day 74） |
| 三角色 | 研究+写作+审校 | 综合（Day 75） |

## 3. 交接物 = 合约

坏做法：Researcher 丢一段散文给 Writer，「你看着办」。

好做法：固定结构，例如今天的 `ResearchBrief`：

| 字段 | 含义 |
|------|------|
| `topic` | 规范化后的主题 |
| `findings` | 若干条带 `source_id` / `claim` / `confidence` 的发现 |
| `researcher_notes` | 给 Writer 的短提示（不是正文） |

Writer 输出 `Article`：`title` / `outline` / `body` / `sources`。  
`sources` 必须来自 Brief 的 `source_id`——**引用可溯源**，为后面 RAG/审校埋伏笔。

## 4. 角色边界（刻意限制）

| 角色 | 可以做 | 不可以做 |
|------|--------|----------|
| Researcher | 检索语料、提炼 findings | 写最终长文 |
| Writer | 读 Brief、组织大纲与正文 | 回头搜语料库 |

为什么？一旦 Writer 也能搜库，两个角色会重新糊成「一个大 Agent」，协调税白付。

前端类比：列表页负责拉数据，详情页只渲染 props——详情页不该再偷偷打列表 API。

## 5. Trace：多智能体的「谁动了这块」

单 Agent 时你看最终答案；多 Agent 时你必须看过程：

```text
[researcher] search → 命中 3 条
[researcher] handoff → findings=3
[writer] draft → sections=3
[writer] done → sources=3
```

调试时先问：是 Research 空了，还是 Writer 没读到 Brief？  
没有 trace，你只会看到「文章很烂」——跟前端没有 Network 面板一样难受。

## 6. 失败要早、要显式

| 情况 | 行为 |
|------|------|
| 主题过短 / 空白 | 启动前失败 |
| 语料无命中 | Researcher 失败（不要交空 Brief） |
| Brief 无 findings | Writer 拒绝（合约违约） |

流水线最怕「空交接还假装成功」。宁可不写，也不产出无来源胡话。

## 7. 今日实现骨架（无 LLM）

练习用确定性启发式代替模型：

1. `search_corpus`：关键词命中语料条目
2. `researcher_run`：把命中变成 `Finding` + notes
3. `writer_run`：按 findings 生成大纲与段落
4. `run_pipeline`：串起来并累积 `trace`

真实项目里，把 2/3 换成 LLM + Tool 即可，**编排形状不变**。

## 8. 与前后日的关系

```text
Day 70：单 Agent 内部 Plan → Execute → Reflect
Day 71：决策——该不该拆成多 Agent
Day 72：若拆，先落地最简单的流水线双 Agent   ← 今天
Day 73：需要路由时，再上主管-工人
```

## 9. 常见坑

| 坑 | 修好 |
|----|------|
| 两个 Agent 共享可变大字典随便改 | 用不可变 Brief/Article 交接 |
| Writer 直接读全局语料 | 删掉它的检索权限 |
| 只测最终正文，不测 trace | 断言角色顺序与 handoff |
| 空 findings 仍生成「看起来完整」的文章 | Writer 入口校验 |

## 10. 今日一句话

> 流水线多智能体 = 专职角色 + 结构化交接 + 可回放 trace；空交接必须失败。

## 11. 明日预告

Day 73：主管-工人模式——一个 Supervisor 按任务类型把活分给不同工人。
