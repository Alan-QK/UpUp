# Day 50 练习说明

## 你要完成什么

实现 `file_assistant.py` 中的 TODO，得到一个**只读**文件助手：

- 工具只有 `list_directory` / `read_file`
- 所有路径必须落在沙箱 `root` 内（防 `../` 越界）
- 用 `ScriptedChat` 跑通 Agent Loop（无真实 LLM）

## 怎么跑

```bash
cd daily/2026-10-01/exercise
python3 -m pip install --user pytest
python3 -m pytest -q
python3 main.py --demo
python3 main.py --escape
```

## 提示

1. 先写 `resolve_sandbox_path`：`Path.resolve()` + `relative_to(root)` 是越界检查的核心
2. 工具失败统一 `ERROR: <ExcName>: <message>` 回填，让模型有机会纠正
3. 不要实现 write/delete——今天的主题就是**权限最小化**
