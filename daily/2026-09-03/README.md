# Day 31｜文档加载与清洗

> 日期：2026-09-03（周四）  
> Phase 2 / Week 7 · 学习日序号：**D31 / 120**  
> 建议时长：**75 分钟**（概念 20 + Coding 50 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说清 RAG 流水线的第一步：把杂乱文件变成**干净、可切分的纯文本**
2. 手写一个 txt/md **文档加载器**（目录扫描 + UTF-8 读取 + 清洗管线）
3. 处理常见脏数据：BOM、换行符、YAML frontmatter、HTML 注释、多余空行
4. 产出带 `source` 元数据的 `Document` 列表，为明天的 Chunking 铺路

---

## 学习内容（20 分钟）

请阅读：

1. [`curriculum/phases/phase-02-prompt-rag.md`](../../curriculum/phases/phase-02-prompt-rag.md)（Week 7 · D31）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾：[`../2026-09-02/notes.md`](../2026-09-02/notes.md)（上周收口 → 本周进入数据层）

重点抓住三件事：

- **Garbage in, garbage out**：切分/向量化之前不清洗，检索噪声会一直放大
- **元数据先挂上**：至少要有 `source`（路径），后面引用溯源才接得上
- **先手写 loader**：别一上来就上 LangChain DocumentLoader；先理解清洗管线

---

## Coding 练习（50 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

今日只用标准库，无需 pydantic / openai。

### 任务

1. 完成 `exercise/doc_loader.py` 中标有 TODO 的函数（`Document` / 常量已给出，勿改字段名）
2. `main.py` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-09-03/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py
python3 main.py --stats
python3 main.py --show note.md
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] 能递归发现 `.txt` / `.md` / `.markdown`，忽略隐藏文件与目录
- [ ] 清洗管线：去 BOM、统一换行、可选去 frontmatter/HTML 注释、折叠空行
- [ ] 每个 `Document` 带 `source`、`suffix`、清洗前后字符数
- [ ] 文件缺失 / 非 UTF-8 解码失败时抛出清晰的 `DocLoadError`
- [ ] 不要引入 langchain / unstructured 等文档解析库

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能画出：目录 → discover → read → clean → `Document[]`
- [ ] 我知道为什么 frontmatter / HTML 注释不该进 embedding（噪声、泄漏元数据）
- [ ] 我能说出：`source` 元数据明天切 chunk 时要跟着走
- [ ] 我清楚明天主题：固定窗口 + overlap 的 Chunking

---

## 通知摘要（便于推送）

**Day 31｜文档加载与清洗**  
实现 txt/md 语料加载器：扫描目录、UTF-8 读取、清洗 BOM/换行/frontmatter/注释，产出带 source 的 Document。  
路径：`daily/2026-09-03/`
