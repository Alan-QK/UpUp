# Day 28 笔记｜从函数到 JSON Schema

## 1. 今天学什么？

Day 26–27 解决的是：**模型输出 → 校验 / 修复**。  
今天反过来：**你的 Python 能力 → 告诉模型「可以调用什么」**。

```text
Python 函数
  → 读签名 + 类型注解 + docstring
    → JSON Schema（parameters）
      → 包进 OpenAI tools[] 条目
        →（Phase 3）模型返回 tool_call → 你本地执行函数
```

前端类比：

| 前端 | 今天 |
|------|------|
| 组件 props 类型 / Zod | 函数参数注解 → JSON Schema |
| OpenAPI 文档里的 requestBody | `parameters` 对象 |
| 后端路由表 | `tools` 列表（name → 实现） |

## 2. 模型看到的长什么样？

OpenAI 兼容接口里，一条 tool 通常是：

```json
{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "查询城市天气。",
    "parameters": {
      "type": "object",
      "properties": {
        "city": { "type": "string", "description": "城市名" },
        "unit": {
          "type": "string",
          "enum": ["celsius", "fahrenheit"],
          "description": "温度单位"
        }
      },
      "required": ["city"]
    }
  }
}
```

注意：

- 顶层永远是 **object**（参数包成一个对象，不是位置参数列表）
- `required` 是「没有默认值、且不是 Optional」的字段名数组
- `Literal[...]` 映射成 `enum`

## 3. 类型怎么映射？

| Python | JSON Schema |
|--------|-------------|
| `str` | `{"type":"string"}` |
| `int` | `{"type":"integer"}` |
| `float` | `{"type":"number"}` |
| `bool` | `{"type":"boolean"}` |
| `list[str]` | `{"type":"array","items":{"type":"string"}}` |
| `dict` | `{"type":"object"}` |
| `Literal["a","b"]` | `{"type":"string","enum":["a","b"]}` |
| `str \| None` / `Optional[str]` | 按 `str` 生成；**参数不进 required** |

工具箱：`typing.get_origin` / `get_args`，再加 `inspect.signature`。

## 4. required 三条规则（今日练习约定）

一个参数进入 `required`，当且仅当：

1. 不是 `self` / `cls`
2. **没有**默认值
3. 注解 **不是** Optional / `| None`

因此：

- `city: str` → required
- `unit: str = "celsius"` → 不进 required（有默认）
- `tag: str | None = None` → 不进 required（Optional + 默认）
- `tag: str | None`（无默认）→ 按今日约定也 **不进** required（类型已声明可空）

## 5. docstring 的两种用途

1. **函数描述**：第一段（到空行或 Args 段）→ `function.description`
2. **参数描述**：`Args:` / `Arguments:` / `参数:` 段里的 `name: 说明` → `properties[name].description`

没有 Args 段也没关系：schema 仍然可用，只是缺 description。

## 6. 为什么今天不用 pydantic？

Day 26 用 pydantic 是为了 **验收模型输出**。  
今天要练的是 **反射生成契约**（Agent 框架底层都在做这件事）。先手写一遍，Phase 3 看框架时才知道它替你省了什么。

## 7. 和 Phase 3 的衔接

| 阶段 | 你做什么 |
|------|----------|
| 今天 | 函数 → schema |
| D42+ | 设计多个 tool schema |
| D43+ | 解析 `tool_calls` 并真正 `fn(**args)` |
| D57 | 白名单 + 参数再校验（schema 两边夹击） |

## 8. 小练习（纸上 2 分钟）

把下面签名脑补成 `parameters`：

```python
def read_file(path: str, max_bytes: int = 4096) -> str: ...
```

答案要点：`properties` 有 `path`(string)、`max_bytes`(integer)；`required` 只有 `["path"]`。
