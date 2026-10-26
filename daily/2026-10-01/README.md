# Day 50｜周挑战：只读文件助手

> 日期：2026-10-01（周四）  
> Phase 3 / Week 10 · 学习日序号：**D50 / 120**  
> 建议时长：**90 分钟**（概念 25 + Coding 60 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 说明 Agent 工具为什么必须做**权限最小化**（只读 vs 读写）
2. 实现路径沙箱：拒绝 `../`、绝对路径越界与空字节注入
3. 提供 `list_directory` + `read_file` 两个只读工具，并把错误统一回填
4. 串起本周 Loop / 终止 / 恢复能力，完成「摸清目录 → 读文件 → 回答」闭环

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-03-agent-core.md`](../../curriculum/phases/phase-03-agent-core.md)（Week 10 · D50）
2. 今日笔记：[`notes.md`](./notes.md)
3. 回顾昨日 Trace：[`../2026-09-30/notes.md`](../2026-09-30/notes.md)

重点抓住三件事：

- **能力 = 攻击面**：多一个 write 工具，就多一类灾难
- **沙箱先于业务**：先 `resolve` 再 I/O，越界直接 `PermissionError`
- **ERROR 可纠正**：越界失败要回填，让模型改读合法路径（呼应 Day 48）

---

## Coding 练习（60 分钟）

目录：[`exercise/`](./exercise/)

### 依赖

```bash
python3 -m pip install --user pytest
```

只用标准库 + pytest。**不要**安装 openai / langchain / pydantic。

### 任务

1. 完成 `exercise/file_assistant.py` 中的 TODO  
   （tool schema / `ScriptedChat` / `default_system_prompt` / `collect_tool_names` **已给齐**）
2. `main.py` 与 `sample_workspace/` **已给齐**，阅读即可
3. 跑通测试：

```bash
cd daily/2026-10-01/exercise
python3 -m pytest -q
```

4. 手工试跑：

```bash
python3 main.py --demo
python3 main.py --escape
```

### 验收标准

- [ ] `pytest` 全部通过（纯本地，无网络）
- [ ] `resolve_sandbox_path` 拒绝 `../` 与沙箱外绝对路径
- [ ] `list_directory` / `read_text_file` 遵守条目数与字节上限
- [ ] 未知工具名与越界读取都回填 `ERROR: ...`
- [ ] `run_readonly_assistant` 支持 final_answer 与 max_steps
- [ ] 全程标准库；工具箱只有 `list_directory` + `read_file`

---

## 参考实现

先自己做。卡住超过 30 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能说清：为什么文件 Agent 默认应该「只读」
- [ ] 我知道 `Path.resolve()` + `relative_to(root)` 如何防目录穿越
- [ ] 我能解释越界 `ERROR` 回填与 Day 48 恢复策略的关系
- [ ] 我已知下周 Day 51：框架选型原则

---

## 本周回顾（Week 10）

| Day | 主题 |
|-----|------|
| 46 | ReAct 与 Agent Loop |
| 47 | 终止条件与步数限制 |
| 48 | 工具错误恢复 |
| 49 | 轨迹日志 Trace |
| **50** | **周挑战：只读文件助手（今天）** |

---

## 通知摘要（便于推送）

**Day 50｜周挑战：只读文件助手**  
给 Agent 加上 list/read 两个只读工具，并用路径沙箱守住权限边界；越界必须失败且可回填纠正。  
路径：`daily/2026-10-01/`
