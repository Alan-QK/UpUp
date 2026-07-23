# Day 4 笔记｜模块化与 pytest 入门

## 1. 前端类比：为什么今天要学这些？

| 前端经验 | Python 对应 |
|----------|-------------|
| `utils/foo.ts` + `export` | `foo.py` + `def` / `class` |
| `packages/shared` | 带 `__init__.py` 的包目录 |
| `import { x } from './utils'` | `from prompt_utils import truncate` |
| Vitest / Jest | **pytest** |
| `expect(fn()).toBe(...)` | `assert fn() == ...` |
| `expect(() => fn()).toThrow()` | `with pytest.raises(...): fn()` |

做 Agent 时，你会拆出大量「可测的小刀」：

- 文本截断、空白规范化
- 从模型回复里抽 `<answer>...</answer>`
- 消息历史裁剪、token 估算

这些函数**不该**和 LLM 调用缠在一起——分开后才能稳定测。

## 2. 模块与包：最小可用心智模型

### 模块（module）

一个 `.py` 文件就是一个模块：

```python
# prompt_utils.py
def truncate(text: str, max_chars: int) -> str:
    ...
```

### 包（package）

带 `__init__.py` 的目录，用来组织多个模块：

```text
agentkit/
  __init__.py      # 可 re-export 公共 API
  prompt_utils.py
  config_io.py
```

```python
# agentkit/__init__.py
from .prompt_utils import truncate

__all__ = ["truncate"]
```

今天练习用**单文件模块**即可；包的概念先建立印象，Week 4 里程碑会用上。

### import 习惯

```python
# 好：从模块导入具体符号
from prompt_utils import truncate, normalize_whitespace

# 慎用：from prompt_utils import *  （污染命名空间）
```

运行测试时，在项目根（`exercise/`）执行 `python -m pytest`，pytest 会把当前目录放进 `sys.path`，所以 `from prompt_utils import ...` 能找到。

## 3. pytest：你真正需要的 20%

### 发现规则

- 文件：`test_*.py` 或 `*_test.py`
- 函数：`test_*`
- 目录：常见放在 `tests/`

### 三种最常用写法

```python
def test_ok() -> None:
    assert truncate("hello", 5) == "hello"


def test_raises() -> None:
    import pytest
    with pytest.raises(ValueError, match="max_chars"):
        truncate("hi", 0)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("a  b", "a b"),
        ("  x\n\ny  ", "x y"),
    ],
)
def test_normalize_param(text: str, expected: str) -> None:
    assert normalize_whitespace(text) == expected
```

### 与「先写实现」的关系

Day 1–3：实现为主，测试已给好。  
**Day 4 起**：你要会自己补测试——这是 Agent 工程的分水岭。

经验法则：

1. 先看函数签名与 docstring（契约）
2. 列 3 类用例：正常 / 边界 / 非法输入
3. 每个用例一个 `test_*`，名字写清意图

## 4. 今日三个工具函数在 Agent 里干嘛用？

| 函数 | 用途直觉 |
|------|----------|
| `normalize_whitespace` | 清洗用户输入 / 日志文本 |
| `truncate` | 控制 prompt 长度，避免撑爆上下文 |
| `extract_tagged_block` | 从模型输出抽结构化片段（简易版） |

它们都是**纯函数**：同输入 → 同输出，无网络、无全局状态 → 单测友好。

## 5. 与前后日的衔接

```text
Day 2–3：模型与配置（数据怎么表达、怎么落盘）
Day 4：  工具函数怎么拆模块、怎么用 pytest 锁行为
Day 5：  周挑战 CLI —— 把模块 + 测试拼成可运行小工具
```

## 6. 今日一句话

> 模块划边界，pytest 锁契约；Agent 再花哨，也要从可测的小函数长出来。

---

## 我的记录（请自己填写）

1.  
2.  
3.  
