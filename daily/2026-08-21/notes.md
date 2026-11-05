# Day 22 笔记｜Few-shot 与反例

## 1. 今天学什么？

Day 21 把 Prompt 拆成角色 / 任务 / 约束 / 格式。  
今天补上分类与抽取里最常用的一块：**示例（shots）**，尤其是 **反例**。

| 术语 | 含义 | 前端类比 |
|------|------|----------|
| Zero-shot | 只给规则，不给样例 | 只写类型定义，不给 Storybook 示例 |
| One-shot | 给 1 条正例 | 一个 canonical demo |
| Few-shot | 给少数几条示例 | Storybook 里覆盖几种变体 |
| 反例 (counter-example) | 「这种**不要**标成 X」 | 边界用例 / 反回归 fixture |

> 记忆口诀：**规则说边界，示例画边界；反例专门防「看起来像」。**

## 2. 为什么分类任务特别需要 few-shot？

纯规则常常不够：

```text
标签：bug / feature / question
请给下面工单分类。
```

模型可能把「能不能加个暗黑模式？」标成 `bug`（因为它带抱怨语气），  
或把「支付失败一直转圈」标成 `question`（因为它以问号结尾）。

加几条 **正例 + 反例** 后，规则变成「可看见的约定」：

```text
【正例】
1. 输入：支付按钮点了没反应，控制台有 500
   标签：bug

【反例】（易混：看起来像 bug，其实不是）
1. 输入：希望支持暗黑模式
   标签：feature
   说明：这是需求，不是缺陷
```

## 3. 怎么写好示例？

### 好示例

- **短**：一条输入 + 一个标签（可选一行说明）
- **对齐真实分布**：覆盖常见写法，而不是文学范文
- **标签集合封闭**：只出现允许的 label
- **正反成对**：每个易混边界至少一条反例

### 差示例

- 示例里出现「大概是 bug 吧」「可能 feature」——标签必须确定
- 10 条几乎重复的正例——浪费 token，不扩大边界
- 反例写成「错误示范作文」却不给正确标签——模型学不会「该标什么」

## 4. 反例不是「负样本堆砌」

反例的目标是：**澄清决策边界**。

| 场景 | 反例要表达的意思 |
|------|------------------|
| 功能请求语气激动 | 「语气差 ≠ bug」 |
| 问怎么用某功能 | 「疑问句 ≠ 一定是 question；若在报错，仍可能是 bug」 |
| 含「失败」二字的赞美 | 「关键词命中 ≠ 标签」 |

写法建议：反例也给出 **正确标签**（而不是只说「不是 bug」）。  
这样 few-shot 始终是「输入 → 标签」的监督学习格式。

## 5. 放在 system 还是 user？

| 内容 | 建议位置 | 原因 |
|------|----------|------|
| 任务、标签集合、输出格式、示例库 | `system` | 相对稳定，可复用 |
| 待分类的本轮文本 | `user` | 每次都变 |

和 Day 21 一致：**system = 说明书；user = 本次工单。**

注意：示例会占 token。生产里常用「每类 1–3 条 + 关键反例」，而不是把整份训练集塞进 Prompt。

## 6. 今日练习的最小 API

```python
spec = ClassificationPrompt(
    task="将用户工单分类到指定标签",
    labels=["bug", "feature", "question"],
    examples=[
        ShotExample("支付失败一直转圈", "bug", kind="positive"),
        ShotExample("希望支持导出 CSV", "feature", kind="positive"),
        ShotExample("怎么重置密码？", "question", kind="positive"),
        ShotExample("暗黑模式什么时候有？", "feature", kind="counter"),
    ],
    output_format="只输出一个标签：bug / feature / question",
)
messages = build_classification_messages(spec, "登录按钮点了没反应")
```

实现时注意：

- `kind` 只允许 `positive` / `counter`（大小写不敏感，内部规范化为小写）
- 示例 `label` 必须落在 `labels` 集合内
- 至少一条 `positive`；`counter` 可以为空
- 渲染顺序：任务 → 标签集合 → 正例 → 反例 → 输出格式
- 空正例节 / 空反例节整节省略（但校验阶段不允许「完全没有正例」）

## 7. 和前端经验的映射

你写过：

```ts
// Storybook：正常态 + 边界态
Primary.story = { args: { loading: false } };
Disabled.story = { args: { disabled: true } };
```

Few-shot 就是 Prompt 版 Storybook：

- **正例** ≈ Happy path stories  
- **反例** ≈ 易错边界 stories  

分类器 Prompt 调优时，优先补「测挂的那条边界」，而不是盲目加长散文说明。

## 8. 明天预告

Day 23 会对比 **思维链（先推理再答）** 与 **直接答案**：何时值得多花 token 换准确率。
