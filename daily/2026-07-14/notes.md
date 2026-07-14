# Day 1 笔记｜环境、项目结构、类型注解

## 1. 为什么前端转 Agent，第一周先补 Python 工程习惯？

你后面会写：

- LLM 客户端封装
- Tool 执行器
- RAG 管线
- FastAPI 服务

这些都不是「单文件脚本思维」能撑住的。Day 1 建立的是：**可安装、可测试、可扩展** 的最小工程感。

前端类比：

| 前端经验 | Python 对应 |
|----------|-------------|
| `npm i` / `pnpm i` | venv + pip / uv |
| `tsconfig` 严格模式 | 类型注解 + 后续 pyright/mypy（先注解） |
| Vitest / Jest | pytest |
| monorepo packages | 清晰目录与模块边界 |

## 2. 虚拟环境（务必建立肌肉记忆）

```bash
# 方式 A：venv
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 方式 B：uv（推荐，后续课程默认提及）
uv venv
source .venv/bin/activate
uv pip install pytest
```

规则：

- 每个项目一个环境
- 依赖写进 `requirements.txt` 或 `pyproject.toml`
- **永远不要**把 API Key 写进代码

## 3. 本课程仓库目录心智模型

```text
curriculum/   → 地图（总纲与阶段）
daily/        → 每日任务（主战场）
exercises/    → 可复用练习脚手架（后续）
projects/     → 里程碑作品
.automation/  → 进度与自动化约定
```

## 4. 类型注解：最小必要子集

```python
def greet(name: str, excited: bool = False) -> str:
    ...
```

常见类型：

- 基础：`str`, `int`, `float`, `bool`
- 容器：`list[str]`, `dict[str, int]`
- 可空：`str | None`
- 结构化：后续用 `dataclass` / `pydantic`（Day 2+）

对 Agent 的直接价值：

- Tool 参数定义更清晰
- 结构化输出更易校验
- 重构时不容易 silently break

## 5. pytest 最小用法

```bash
pytest -q
```

测试文件：`test_*.py`，测试函数：`test_*`。

断言：

```python
assert greet("Ada") == "Hello, Ada"
```

异常：

```python
import pytest

with pytest.raises(ValueError):
    greet("")
```

## 6. 今日一句话

> 先把 Python 写成「有类型、有测试的小模块」，再谈 Agent。

---

## 我的记录（请自己填写）

1.  
2.  
3.  
