# Day 3｜文件 I/O、JSON 与 pathlib

> 日期：2026-07-22（周三）  
> Phase 1 / Week 1 · 学习日序号：**D3 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 用 `pathlib.Path` 处理路径（替代到处拼字符串）
2. 安全读写 JSON 文件（编码、父目录、原子感习惯）
3. 把「JSON dict ↔ dataclass」接起来，并做基础校验
4. 理解：Agent 的配置/记忆/轨迹，几乎都从文件与序列化开始

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 1 部分）
2. 今日笔记：[`notes.md`](./notes.md)

重点抓住三件事：

- **Path 是对象，不是字符串**：`path / "config.json"`、`path.exists()`、`path.read_text()`
- **JSON 是边界格式**：进内存立刻变成 dataclass，出内存再 dump
- **读配置必校验**：文件缺失、JSON 非法、字段缺失，都要变成可分支异常

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 任务

实现一个迷你「Agent JSON 配置读写」模块：

1. 完成 `exercise/config_io.py` 中的 TODO
2. （可选）对照 `exercise/models.py`，无需改动
3. 运行测试：

```bash
cd daily/2026-07-22/exercise
pip install pytest   # 或 uv pip install pytest
python -m pytest -q
```

4. 运行手工脚本：

```bash
python main.py
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] 使用 `pathlib.Path`，不手写一堆 `os.path.join`
- [ ] 能加载 / 保存 `AgentConfig` 到 JSON
- [ ] 文件不存在、JSON 非法、字段非法时抛出自定义 `ConfigError`
- [ ] 你能用一句话说明：为什么配置读入后要立刻变成 dataclass

---

## 参考实现

先自己做。卡住超过 15 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我知道 `Path` 的 `/` 拼接与 `read_text` / `write_text`
- [ ] 我能解释 `json.loads` 与 `json.load` 的差别
- [ ] 我能处理「文件不存在」和「JSON 解析失败」两类错误
- [ ] 我已知下一步是 Day 4：模块化与 pytest 入门

---

## 通知摘要（便于推送）

**Day 3｜文件 I/O、JSON 与 pathlib**  
用 pathlib 读写 Agent JSON 配置，并做基础校验，跑通 pytest。  
路径：`daily/2026-07-22/`
