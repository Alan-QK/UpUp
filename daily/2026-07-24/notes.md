# Day 5 笔记｜周挑战：迷你 CLI 工具

## 1. 今天为什么是「周挑战」？

Week 1 不是学五堆碎片，而是攒齐 Agent 工程的地基：

| Day | 能力 | 今天用在哪 |
|-----|------|-----------|
| D1 | 项目结构 / 类型注解 | `Note`、函数签名 |
| D2 | dataclass / 异常 | `Note`、`NoteNotFoundError` |
| D3 | pathlib + JSON | `notes.json` 读写 |
| D4 | 模块 + pytest | `note_store` 可单测 |
| D5 | **CLI 端到端** | `argparse` 把能力交给用户 |

前端类比：你已经写了 utils / models / 单测，今天补一个「命令行版页面入口」。

## 2. 架构：薄 CLI + 厚 Store

```text
用户敲命令
    ↓
main.py（argparse：解析 argv）
    ↓
note_store.py（业务：增删查 + 持久化）
    ↓
notes.json
```

**好习惯**：

- store 不知道「怎么打印」
- CLI 不知道「JSON 长什么样」
- 测试只打 store（快、稳、不依赖终端）

以后做 Agent CLI（`/reset`、`/exit`、调工具）也是同一拆法。

## 3. argparse 子命令：最小心智模型

```python
parser = argparse.ArgumentParser(prog="notes")
sub = parser.add_subparsers(dest="command", required=True)

add_p = sub.add_parser("add")
add_p.add_argument("title")
add_p.add_argument("body")

# python main.py add "标题" "正文"
```

对应前端直觉：

| CLI | 前端 |
|-----|------|
| 子命令 `add` / `list` | 路由 `/notes/add` |
| 位置参数 | path / query |
| `--file` 选项 | 全局配置 |

## 4. 持久化约定（够用就好）

文件形态示例：

```json
{
  "next_id": 3,
  "notes": [
    {"id": 1, "title": "A", "body": "...", "created_at": "2026-07-24T10:00:00+08:00"},
    {"id": 2, "title": "B", "body": "...", "created_at": "2026-07-24T10:05:00+08:00"}
  ]
}
```

规则建议：

1. 文件不存在 → 当作空库（`next_id=1, notes=[]`）
2. `add` 后立刻写盘（简单可靠；不必上数据库）
3. `delete` 找不到 id → 明确异常，而不是静默成功
4. `search` 对 title/body **大小写不敏感**包含匹配即可

## 5. 测试策略（周挑战也要测）

优先测 store，不测「打印漂不漂亮」：

- `add` 后 `list` 能看到
- `get` 存在 / 不存在
- `delete` 后无法再 `get`
- `search` 命中与空结果
- 换一个进程语义：重新 `NoteStore(同一路径)` 仍能读到（持久化）

用 pytest 的 `tmp_path`，避免污染仓库。

## 6. 本周收口一句话

> 能落盘、能校验、能单测的小模块，才配接上 LLM；CLI 只是把模块交到手上的握把。

## 7. 下周预告

Week 2 进入网络层：`httpx`、超时重试、`asyncio`、密钥管理——为第一次调 LLM API 铺路。

---

## 我的记录（请自己填写）

1.  
2.  
3.  
