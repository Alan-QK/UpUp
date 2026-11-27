# Day 32 笔记｜文本切分 Chunking

## 1. 今天在 RAG 里的位置

```text
文件目录
  → 加载 & 清洗（昨天 Document）
    → Chunking（今天）
      → Embedding（明天）
        → 向量库写入 / 检索
```

检索不是拿整本书去比相似度，而是拿一块块「可嵌入、可引用」的片段。今天把 Document 切成 Chunk。

## 2. 前端类比

| 前端 | Chunking |
|------|----------|
| 虚拟列表按窗口渲染 | 长文按窗口切块 |
| 轮播/分页有 overlap 预取 | 相邻 chunk 重叠几句，避免切缝丢语义 |
| 列表项带 `id` + 绝对偏移 | Chunk 带 `source` + `start`/`end` |

你熟悉的「大数据不要一次塞进内存」——RAG 里是「大上下文不要一次塞进检索」。

## 3. 固定窗口 + overlap

三个参数：

| 参数 | 含义 |
|------|------|
| `chunk_size` | 每块最多多少字符 |
| `overlap` | 相邻两块重叠多少字符 |
| `step` | `chunk_size - overlap`，每次窗口前进多少 |

示意（`chunk_size=8`, `overlap=2`, `step=6`）：

```text
索引:  0123456789ABCDEF...
块0:   [=======]          start=0  end=8
块1:         [=======]    start=6  end=14
块2:               [===…] start=12 …
              ^^ overlap
```

原则：

- `chunk_size < 1` 非法
- `overlap < 0` 非法
- `overlap >= chunk_size` 非法（否则 step≤0，死循环或原地踏步）

## 4. Chunk 最小字段

```text
source      # 继承 Document.source，引用溯源用
index       # 同一 source 内从 0 递增
start / end # 相对原文的半开区间 [start, end)
text        # 切片内容 = text[start:end]
char_count  # len(text)，方便统计
```

半开区间和前端 `slice(start, end)`、Python `s[a:b]` 一致——`end` 不包含。

## 5. 边界行为（今天练习约定）

1. **空字符串** → `[]`
2. **长度 ≤ chunk_size** → 恰好 1 块，`start=0`, `end=len(text)`
3. **滑到末尾**：`end = min(start + chunk_size, n)`；当 `end == n` 后停止，不再开新窗
4. **多文档**：每个 Document 独立切分，`index` 各自从 0 计；合并语料时按文档顺序拼接 chunk 列表

## 6. 多大合适？（先建立直觉）

| 倾向 | 后果 |
|------|------|
| chunk 过大（如 4000+ 字） | 检索命中一块，但噪声多、贵、难精确定位 |
| chunk 过小（如 50 字） | 语义破碎，「主语在上一块、谓语在下一块」 |
| overlap 过小 | 关键句跨缝时两边都不完整 |
| overlap 过大 | 冗余高、embedding 次数↑、费用↑ |

入门默认可以记：**size≈200–500 字符，overlap≈10%–20%**。真实项目再按语种/文档类型调。

> 今天用「字符数」而不是 token，是为了零依赖练算法；上线前通常按 tokenizer 切。

## 7. 和「递归/语义切分」的关系

LangChain 的 RecursiveCharacterTextSplitter、按标题/段落切，本质仍是：选切点 → 控大小 → 可选 overlap → 挂 metadata。  
固定窗口是最笨也最透明的基线；先写对它，再换策略才知道差在哪。

## 8. 纸上 30 秒

原文长度 20，`chunk_size=10`，`overlap=3`：

- `step = 7`
- 块 0：`[0,10)`，块 1：`[7,17)`，块 2：`[14,20)` —— 然后停

问：为什么没有块从 21 开始？  
答：上一块已经 `end == n`，全文覆盖完毕。
