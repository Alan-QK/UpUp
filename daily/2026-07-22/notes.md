# Day 3 笔记｜文件 I/O、JSON、pathlib

## 1. 前端类比：为什么今天要学这些？

| 前端经验 | Python 对应 |
|----------|-------------|
| `fs.readFile` / `fs.promises` | `Path.read_text()` / `open(...)` |
| `path.join(a, b)` | `Path(a) / b` |
| `JSON.parse` / `JSON.stringify` | `json.loads` / `json.dumps` |
| `zod.parse(config)` | 读完 JSON 后立刻校验并转 dataclass |
| `import config from './config.json'` | 显式 `load_agent_config(path)` |

后面做 Agent 时，你会不断遇到：

- `agent.config.json` / `tools.json`
- prompt 模板文件
- 对话记忆、评测数据集、运行轨迹（trace）落盘

今天练的是这些东西的**读写骨架**。

## 2. pathlib：把路径当对象

```python
from pathlib import Path

root = Path(__file__).resolve().parent
config_path = root / "fixtures" / "agent.json"

print(config_path.exists())
text = config_path.read_text(encoding="utf-8")
```

要点：

- 优先 `pathlib`，少用字符串拼路径
- `Path(__file__).parent`：以「当前文件」定位资源，比 `cwd` 稳
- 读写文本时显式 `encoding="utf-8"`（跨平台别踩坑）
- 写文件前可 `path.parent.mkdir(parents=True, exist_ok=True)`

## 3. JSON：边界格式，不是业务模型

```python
import json
from pathlib import Path

raw = json.loads(Path("a.json").read_text(encoding="utf-8"))
# raw 是 dict / list —— 类型很松

Path("b.json").write_text(
    json.dumps(raw, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
```

| API | 用途 |
|-----|------|
| `json.loads(str)` / `json.dumps(obj)` | 字符串 ↔ Python 对象 |
| `json.load(fp)` / `json.dump(obj, fp)` | 文件对象 ↔ Python 对象 |

经验法则：

- **进内存立刻建模**：`dict` → `AgentConfig`
- **出内存再序列化**：`AgentConfig` → `dict` → JSON
- `ensure_ascii=False`：中文可读；`indent=2`：便于人工改配置

## 4. 错误要可分支

读配置时至少区分：

1. **文件不存在** → `ConfigError("config not found: ...")`
2. **JSON 非法** → `ConfigError("invalid json: ...")`
3. **字段不合法** → `ConfigError("model must not be empty")` 等

坏味道：

```python
data = json.load(open("config.json"))  # 路径、编码、关闭、异常全糊在一起
```

更好：用 `Path` + 明确异常包装，调用方才能决定「提示用户」还是「用默认配置」。

## 5. 与 Day 2 的衔接

Day 2：`AgentConfig` + `ConfigError` 描述「配置长什么样、哪里坏了」。  
Day 3：把同一份配置从磁盘装进来、写回去。

```text
disk JSON  --load-->  dict  --validate-->  AgentConfig  --save-->  disk JSON
```

后面 RAG / Agent 的「记忆文件」「工具清单」都是这条流水线的变体。

## 6. 今日一句话

> Path 管「在哪」，JSON 管「怎么过边界」，dataclass 管「进来之后是什么」。

---

## 我的记录（请自己填写）

1.  
2.  
3.  
