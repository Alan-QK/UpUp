"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, MutableMapping


class EnvError(ValueError):
    """环境变量或 .env 文件不合法。"""


def parse_dotenv(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in raw_line:
            raise EnvError(f"invalid line: {raw_line}")
        key_part, value_part = raw_line.split("=", 1)
        key = key_part.strip()
        if not key:
            raise EnvError("empty key")
        value = value_part.rstrip("\r\n")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        else:
            value = value.strip()
        result[key] = value
    return result


def load_dotenv(
    path: Path,
    *,
    environ: MutableMapping[str, str] | None = None,
    override: bool = False,
) -> dict[str, str]:
    if not path.is_file():
        raise EnvError(f"env file not found: {path}")
    loaded = parse_dotenv(path.read_text(encoding="utf-8"))
    target: MutableMapping[str, str] = os.environ if environ is None else environ
    for key, value in loaded.items():
        if override or key not in target:
            target[key] = value
    return loaded


def get_env(
    name: str,
    default: str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> str | None:
    source = os.environ if environ is None else environ
    if name not in source:
        return default
    return source[name]


def require_env(
    name: str,
    *,
    environ: Mapping[str, str] | None = None,
) -> str:
    source = os.environ if environ is None else environ
    value = source.get(name, "").strip()
    if not value:
        raise EnvError(f"missing required env: {name}")
    return value


def mask_secret(value: str, *, head: int = 4, tail: int = 4) -> str:
    text = value.strip()
    if not text or len(text) <= head + tail:
        return "***"
    return f"{text[:head]}…{text[-tail:]}"


@dataclass(frozen=True)
class LlmSettings:
    api_key: str
    base_url: str
    model: str


def load_llm_settings(*, environ: Mapping[str, str] | None = None) -> LlmSettings:
    source = os.environ if environ is None else environ
    api_key = require_env("OPENAI_API_KEY", environ=source)

    raw_base = get_env("OPENAI_BASE_URL", environ=source)
    base_url = (
        raw_base.strip()
        if raw_base is not None and raw_base.strip()
        else "https://api.openai.com/v1"
    )

    raw_model = get_env("OPENAI_MODEL", environ=source)
    model = (
        raw_model.strip()
        if raw_model is not None and raw_model.strip()
        else "gpt-4o-mini"
    )

    return LlmSettings(api_key=api_key, base_url=base_url, model=model)
