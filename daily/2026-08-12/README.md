# Day 17｜采样参数实验

> 日期：2026-08-12（周三）  
> Phase 1 / Week 4 · 学习日序号：**D17 / 120**  
> 建议时长：**75 分钟**（概念 25 + Coding 45 + 自检 5）

---

## 今日目标

学完今天，你能够：

1. 用自己的话解释 `temperature` / `top_p` 对输出风格的影响
2. 校验参数合法区间，并实现同一 Prompt 的 **temperature 扫描**
3. 用廉价文本指标 + 报告格式，把「感觉更随机」变成可对比结果
4. 知道 Agent 里哪些步骤该低温、哪些可以升温

---

## 学习内容（25 分钟）

请阅读：

1. [`curriculum/phases/phase-01-python-llm.md`](../../curriculum/phases/phase-01-python-llm.md)（Week 4）
2. 今日笔记：[`notes.md`](./notes.md)
3. 可选：回顾 Day 11 `complete(..., temperature=)` 如何写入请求体

重点抓住三件事：

- **先固定 Prompt，再扫参数**，否则对比无意义
- temperature / top_p **别同时猛拧**
- 结构化任务偏低随机性；创意任务可以高一点

---

## Coding 练习（45 分钟）

目录：[`exercise/`](./exercise/)

### 任务

1. 完成 `exercise/sampling_lab.py` 中的 TODO
2. `chat_client.py` / `main.py` **已给齐**，无需改
3. 跑通测试：

```bash
cd daily/2026-08-12/exercise
python3 -m pytest -q
```

若尚未安装依赖：

```bash
python3 -m pip install --user httpx pytest
```

4. 手工试跑（离线 Demo）：

```bash
python3 main.py --demo
python3 main.py --demo -t 0.0,1.0,2.0 --top-p 0.9
```

### 验收标准

- [ ] `pytest` 全部通过
- [ ] `validate_temperature` / `validate_top_p` 边界清晰
- [ ] `run_temperature_sweep` 按序调用，并把 `temperature`/`top_p` 传给客户端
- [ ] `unique_token_ratio` / `jaccard_distance` 行为符合笔记约定
- [ ] `format_comparison_report` 含标题、每档摘要，以及成对 Jaccard 节
- [ ] `--demo` 能打印出三档 temperature 的对比报告

---

## 参考实现

先自己做。卡住超过 20 分钟再看：[`solution/`](./solution/)

---

## 自检清单

- [ ] 我能向同事解释：为什么抽 JSON 时不要随便把 temperature 拉到 1.5
- [ ] 我知道 top_p 与 temperature 都影响随机性，所以要避免双旋钮乱拧
- [ ] 我能说清报告里 `unique_token_ratio` 与 Jaccard 距离各自粗测什么
- [ ] 我已知明天 Day 18：模型 Provider 抽象（可替换 ChatClient）

---

## 通知摘要（便于推送）

**Day 17｜采样参数实验**  
同一 Prompt 扫描多档 temperature，计算简易多样性指标并输出对比报告；搞清低温稳健 / 高温发散。  
路径：`daily/2026-08-12/`
