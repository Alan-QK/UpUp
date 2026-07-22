"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models import AgentConfig


class ConfigError(ValueError):
    """配置文件或配置内容不合法。"""


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"config not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid json: {path}") from exc
    if not isinstance(data, dict):
        raise ConfigError("config root must be an object")
    return data


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


def _validate_agent_dict(data: dict[str, Any]) -> AgentConfig:
    if "model" not in data:
        raise ConfigError("model must not be empty")

    model = data["model"]
    if not isinstance(model, str):
        raise ConfigError("model must not be empty")
    cleaned_model = model.strip()
    if not cleaned_model:
        raise ConfigError("model must not be empty")

    temperature: float = 0.2
    if "temperature" in data:
        raw_temp = data["temperature"]
        if not isinstance(raw_temp, (int, float)) or isinstance(raw_temp, bool):
            raise ConfigError("temperature must be a number")
        temperature = float(raw_temp)
        if not 0 <= temperature <= 2:
            raise ConfigError("temperature out of range")

    max_tokens: int = 1024
    if "max_tokens" in data:
        raw_tokens = data["max_tokens"]
        if isinstance(raw_tokens, bool) or not isinstance(raw_tokens, int):
            raise ConfigError("max_tokens must be an int")
        if raw_tokens < 1:
            raise ConfigError("max_tokens must be >= 1")
        max_tokens = raw_tokens

    return AgentConfig(
        model=cleaned_model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def load_agent_config(path: Path) -> AgentConfig:
    return _validate_agent_dict(load_json(path))


def save_agent_config(path: Path, config: AgentConfig) -> None:
    save_json(path, config.to_dict())
