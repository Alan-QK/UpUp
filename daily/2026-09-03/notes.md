# Day 31 笔记｜文档加载与清洗

## 1. 今天在 RAG 里的位置

Week 7 开始搭 **RAG 数据层**：

```text
文件目录
  → 加载 & 清洗（今天）
  → Chunking（明天）
  → Embedding
  → 向量库写入 / 检索
```

没有干净文本，后面全是噪音。今天只做 loader，不碰模型。

## 2. 前端类比

| 前端 | RAG 数据层 |
|------|------------|
| 拉取 API → normalize → store | 读文件 → clean → Document |
| 列表项带 `id` / `url` | Document 带 `source` |
| 去掉 HTML 标签再展示 | 去掉 frontmatter / 注释再切分 |

你熟悉的「进入状态树前先 normalize」——今天就是这件事。

## 3. 清洗管线（建议顺序）

1. **去 BOM**（`\ufeff`）：部分编辑器保存 UTF-8 带 BOM，会污染第一个 token
2. **统一换行**：`\r\n` / `\r` → `\n`（跨平台一致）
3. **去 YAML frontmatter**：Markdown 开头的 `--- ... ---` 元数据块（标题/标签等）通常不进正文检索
4. **去 HTML 注释**：`<!-- ... -->` 常是编辑残留
5. **折叠空行**：连续空行压到上限（默认 2），并去掉行尾空格

原则：**改脏、不改义**。不要在这一步做摘要或改写。

## 4. Document 最小字段

```text
source   # 相对路径（posix），用于引用溯源
text     # 清洗后正文
suffix   # .txt / .md / .markdown
raw_char_count / char_count  # 清洗前后，便于观察「洗掉了多少」
```

后续 chunk 会继承 `source`；Day 37 做引用溯源时会用到。

## 5. 发现文件时的边界

- 只收白名单后缀：`.txt` / `.md` / `.markdown`
- **递归**扫描，但跳过以 `.` 开头的文件/目录（如 `.git`、`.DS_Store`）
- 结果按相对路径排序 → 测试与演示可复现
- 编码：今日统一 **UTF-8**；解码失败要早失败（`DocLoadError`），别静默吞掉

## 6. 和「解析库」的关系

LangChain / LlamaIndex 的 DocumentLoader 本质也是：读字节 → 解码 → 可选清洗 → 挂 metadata。  
先手写一遍，再用框架时你知道它藏了哪些坑（编码、隐藏文件、frontmatter）。

## 7. 纸上 30 秒

一篇 md 开头是：

```markdown
---
title: 请假制度
---

正文第一段
```

问：进 embedding 的正文应从哪一行开始？  
答：从「正文第一段」——frontmatter 应在清洗阶段剥掉。
