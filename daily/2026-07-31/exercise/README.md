# Day 9 练习说明

```bash
python3 -m pytest -q
python3 main.py
```

今日重点：

1. `env_loader.py` — **请你实现** `parse_dotenv` / `load_dotenv` / `get_env` / `require_env` / `mask_secret` / `load_llm_settings`
2. `main.py` — 演示已搭好：读 `sample.env`，打印脱敏配置
3. 只用标准库（`os` / `pathlib` / `dataclasses`），不要安装 `python-dotenv`
4. 测试用临时文件与假 `environ` dict，不会碰你本机真实密钥
