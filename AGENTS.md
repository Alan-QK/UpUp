# AGENTS.md

## Cursor Cloud specific instructions

本仓库是「前端 → AI Agent 转型学习计划」文档 + 每日 Python 练习集合，不是一个长驻服务型应用。

### 运行环境
- 语言：Python 3.11+（VM 上为 Python 3.12，命令用 `python3`，无 `python` 软链接）。
- 唯一依赖：`pytest`（由 update script 安装到 `~/.local/bin`，未加入 PATH）。用 `python3 -m pytest` 调用，不要直接用 `pytest`。
- 无 lint / 类型检查工具配置（`.gitignore` 提到 `.ruff_cache`/`.mypy_cache` 但仓库未配置 ruff/mypy），因此没有 lint 步骤可跑。

### 练习/测试如何跑
- 每个练习是独立目录 `daily/YYYY-MM-DD/exercise/`，内含 `main.py`、模块文件和 `tests/`。测试用相对导入（如 `from greeter import ...`），必须 **在该 exercise 目录内** 运行：
  ```bash
  cd daily/2026-07-21/exercise && python3 -m pytest -q
  ```
- 重要：`exercise/` 里的模块是留有 `TODO`/`NotImplementedError` 的**学习脚手架**，未完成时 `pytest` 与 `python3 main.py` **预期失败**，这不是环境问题。
- 参考实现在同级 `solution/` 目录，但 `solution/` 内**没有** `tests/` 和 `main.py`。若要跑通绿灯，需把 `solution/` 的模块与 `exercise/tests/`（及 `main.py`）放到同一目录再运行（例如复制到临时目录），否则 solution 无法被测试直接引用。
