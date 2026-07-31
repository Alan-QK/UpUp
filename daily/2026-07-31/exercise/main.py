"""Day 9 手工运行入口：加载 sample.env，打印脱敏后的 LLM 配置。"""

from __future__ import annotations

from pathlib import Path

from env_loader import load_dotenv, load_llm_settings, mask_secret

SAMPLE_ENV = Path(__file__).with_name("sample.env")


def main() -> None:
    loaded = load_dotenv(SAMPLE_ENV, override=True)
    settings = load_llm_settings()
    print(f"loaded keys: {sorted(loaded)}")
    print(f"base_url   : {settings.base_url}")
    print(f"model      : {settings.model}")
    print(f"api_key    : {mask_secret(settings.api_key)}")
    print("ok — 密钥只出现在环境里，日志里是脱敏形态。")


if __name__ == "__main__":
    main()
