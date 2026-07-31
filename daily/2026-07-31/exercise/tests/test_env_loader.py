"""Day 9：env_loader 测试（不读写真实机器密钥）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from env_loader import (
    EnvError,
    LlmSettings,
    get_env,
    load_dotenv,
    load_llm_settings,
    mask_secret,
    parse_dotenv,
    require_env,
)


def test_parse_dotenv_basic_and_comments() -> None:
    text = """
# comment
OPENAI_API_KEY=sk-abc

OPENAI_MODEL=gpt-4o-mini
"""
    assert parse_dotenv(text) == {
        "OPENAI_API_KEY": "sk-abc",
        "OPENAI_MODEL": "gpt-4o-mini",
    }


def test_parse_dotenv_quotes_and_override() -> None:
    text = """
NAME="Alice Wonder"
NAME='Bob'
PATH_VAL=/tmp/demo
"""
    assert parse_dotenv(text) == {
        "NAME": "Bob",
        "PATH_VAL": "/tmp/demo",
    }


def test_parse_dotenv_invalid_line() -> None:
    with pytest.raises(EnvError, match="invalid line"):
        parse_dotenv("NO_EQUALS_HERE\n")


def test_parse_dotenv_empty_key() -> None:
    with pytest.raises(EnvError, match="empty key"):
        parse_dotenv("=value\n")


def test_load_dotenv_respects_override(tmp_path: Path) -> None:
    path = tmp_path / "a.env"
    path.write_text("TOKEN=from-file\nNAME=file\n", encoding="utf-8")
    environ = {"TOKEN": "from-process"}

    loaded = load_dotenv(path, environ=environ, override=False)
    assert loaded == {"TOKEN": "from-file", "NAME": "file"}
    assert environ == {"TOKEN": "from-process", "NAME": "file"}

    load_dotenv(path, environ=environ, override=True)
    assert environ["TOKEN"] == "from-file"


def test_load_dotenv_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nope.env"
    with pytest.raises(EnvError, match="env file not found"):
        load_dotenv(missing, environ={})


def test_get_env_and_require_env() -> None:
    environ = {"A": "x", "B": "  ", "C": "  hi  "}
    assert get_env("A", environ=environ) == "x"
    assert get_env("MISSING", "fallback", environ=environ) == "fallback"
    assert require_env("C", environ=environ) == "hi"
    with pytest.raises(EnvError, match="missing required env: B"):
        require_env("B", environ=environ)
    with pytest.raises(EnvError, match="missing required env: Z"):
        require_env("Z", environ=environ)


def test_mask_secret() -> None:
    assert mask_secret("sk-demo-very-long-secret-key") == "sk-d…-key"
    assert mask_secret("short") == "***"
    assert mask_secret("12345678") == "***"
    assert mask_secret("123456789") == "1234…6789"
    assert mask_secret("   ") == "***"


def test_load_llm_settings_defaults_and_required() -> None:
    with pytest.raises(EnvError, match="OPENAI_API_KEY"):
        load_llm_settings(environ={})

    settings = load_llm_settings(
        environ={
            "OPENAI_API_KEY": " sk-test ",
            "OPENAI_BASE_URL": "  ",
            "OPENAI_MODEL": "",
        }
    )
    assert settings == LlmSettings(
        api_key="sk-test",
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
    )

    custom = load_llm_settings(
        environ={
            "OPENAI_API_KEY": "sk-x",
            "OPENAI_BASE_URL": "https://example.com/v1",
            "OPENAI_MODEL": "deepseek-chat",
        }
    )
    assert custom.base_url == "https://example.com/v1"
    assert custom.model == "deepseek-chat"
