# Day 17 练习｜采样参数实验

## 你要改什么

只改：`sampling_lab.py`（所有 `TODO` / `NotImplementedError`）

已给齐、一般不用动：

- `chat_client.py`（含可选 `top_p`）
- `main.py`
- `tests/`

## 依赖

```bash
python3 -m pip install --user httpx pytest
```

## 怎么跑

```bash
cd daily/2026-08-12/exercise
python3 -m pytest -q
python3 main.py --demo
python3 main.py --demo -t 0.0,1.0,2.0
```

真调模型时请先导出 `OPENAI_API_KEY`（可选 `OPENAI_BASE_URL` / `OPENAI_MODEL`），去掉 `--demo`。
