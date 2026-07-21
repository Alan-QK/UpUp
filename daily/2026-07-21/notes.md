# Day 2 笔记｜函数、dataclass、Enum、异常设计

## 1. 前端类比：为什么今天要学这些？

| 前端经验 | Python 对应 |
|----------|-------------|
| `type User = { id: string; role: 'admin' \| 'user' }` | `@dataclass` + `Enum` |
| Zod / Yup 校验 | 显式校验函数 + 自定义异常 |
| `throw new Error('...')` 到处飞 | 分层异常：`ValidationError` / `ConfigError` |
| 配置对象传入组件 | `AgentConfig` 传入 LLM / Agent 运行时 |

后面做 Agent 时，你会不断遇到：

- system prompt / temperature / model 名
- 用户身份与权限
- 工具参数校验失败

今天练的是这些东西的**最小骨架**。

## 2. dataclass：结构化数据的默认选择

```python
from dataclasses import dataclass

@dataclass
class AgentConfig:
    model: str
    temperature: float = 0.2
    max_tokens: int = 1024
```

要点：

- 自动生成 `__init__` / `__repr__` / `__eq__`
- 字段要有类型注解
- 有默认值的字段必须写在无默认值字段后面
- 需要可变默认值时用 `field(default_factory=list)`，不要写 `items: list = []`

对 Agent 的价值：配置、消息、工具调用结果都可以先用 dataclass 表达，再逐步升级到 Pydantic（Phase 2）。

## 3. Enum：消灭魔法字符串

```python
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
```

继承 `str, Enum` 的好处：序列化/打印时行为更接近字符串，后续写 JSON 时更省事。

## 4. 异常设计：给调用方「可分支」的信息

坏味道：

```python
raise Exception("坏了")
```

更好：

```python
class ValidationError(ValueError):
    """输入数据不合法（可修复的调用方错误）。"""


class ConfigError(ValueError):
    """配置不合法（启动或装配阶段错误）。"""
```

经验法则：

- **ValidationError**：某个字段/参数不对（name 为空、temperature 超范围）
- **ConfigError**：整份配置无法用于启动 Agent（model 为空、关键缺失等——今天先做字段级）
- 继承 `ValueError` 是务实选择：pytest / 调用方仍可用宽捕获，但优先捕获具体类型

## 5. 函数：签名即契约

```python
def create_user(user_id: str, name: str, role: Role) -> User:
    ...
```

写函数时先问三句：

1. 合法输入长什么样？
2. 非法输入抛什么？
3. 成功时返回什么？

Agent 工具函数尤其需要这套纪律——模型乱传参时，你要稳定地失败，而不是 silent wrong。

## 6. 今日一句话

> 用 dataclass 描述「是什么」，用异常描述「哪里坏了」，用函数把两者接到一起。

---

## 我的记录（请自己填写）

1.  
2.  
3.  
