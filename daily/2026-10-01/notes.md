# Day 50 笔记｜周挑战：只读文件助手

## 1. 为什么今天做「文件助手」？

Week 10 前四天打好了 Agent 骨架：

| Day | 能力 |
|-----|------|
| 46 | Loop 跑起来 |
| 47 | 预算内停得住 |
| 48 | 工具错了能纠正 |
| 49 | 过程留得下 Trace |

周挑战要落到一个**真实危险域**：文件系统。  
模型一旦能写文件，幻觉就不再只是「说错话」，而可能是「改坏仓库」。

所以今天的产品约束写死为：**只读**。

## 2. 前端迁移直觉

| 前端 / Web | 文件 Agent |
|------------|------------|
| 只读 API vs 管理后台写接口 | `list`/`read` vs `write`/`delete` |
| CORS / CSP 缩小攻击面 | 工具白名单缩小能力面 |
| 路径规范化防 open redirect | `resolve` + root 前缀检查 |
| 403 Forbidden | `PermissionError` → `ERROR:` 回填 |
| Feature flag 默认关闭危险能力 | 默认不给写工具 |

你在前端做过的「最小权限」，原样搬到 Tool Schema 设计即可。

## 3. 权限边界三原则

1. **默认拒绝**：不在白名单的工具名直接 `Unknown tool`
2. **先解析，后 I/O**：任何 path 先 `resolve_sandbox_path`
3. **失败可观察**：越界不要静默 `""`，要 `ERROR: PermissionError: ...`

## 4. 路径沙箱怎么做（核心）

```python
root = root.resolve()
target = (root / user_path).resolve()  # 或绝对路径直接 resolve
target.relative_to(root)               # 失败 → 越界
```

常见攻击：

| 输入 | 意图 |
|------|------|
| `../.env` | 目录穿越 |
| `/etc/passwd` | 绝对路径逃逸 |
| `docs/../../outside.txt` | 叠加 `..` |
| `a\x00.txt` | 空字节截断（部分生态历史坑） |

全部应在进 `open()` 之前被挡下。

## 5. 两个只读工具

```text
list_directory(path=".")  → {path, entries:[{name,type}], truncated?}
read_file(path="...")     → {path, content, truncated, bytes_read}
```

上限很重要：

- `max_list_entries`：防止一次列出巨型目录撑爆上下文
- `max_read_bytes`：防止把 200MB 日志塞进 prompt

这和前端列表分页 / 接口 response size limit 是同一类工程意识。

## 6. 和 Loop 怎么接

```text
user: 笔记里写了什么？
 → list_directory(".")
 ← entries: README.md, docs, src
 → read_file("docs/notes.md")
 ← content: ...
 → final: 笔记强调权限边界……
```

越界演示：

```text
 → read_file("../outside.txt")
 ← ERROR: PermissionError: path escapes sandbox
 → read_file("README.md")
 ← content: ...
 → final: 已改为读取沙箱内 README
```

这就是 Day 48「错误恢复」在文件系统场景的落地。

## 7. 明确不做的事（今天）

- 不写文件、不删文件、不 `os.system`
- 不跟随危险 symlink 逃逸（`resolve()` 后仍要 `relative_to`）
- 不上真实 LLM（继续 `ScriptedChat`，保证可测）

下周 Day 51 开始看框架选型——你会更清楚：框架帮你省的是样板代码，**权限模型仍要自己想清楚**。

## 8. 自检口诀

> 工具越少越安全；路径先 resolve；错误要回填；写能力默认关。
