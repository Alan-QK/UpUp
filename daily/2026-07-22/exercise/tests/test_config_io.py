"""Day 3：JSON 配置读写测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from config_io import (
    ConfigError,
    load_agent_config,
    load_json,
    save_agent_config,
    save_json,
)
from models import AgentConfig


def test_load_json_ok(tmp_path: Path) -> None:
    path = tmp_path / "a.json"
    path.write_text('{"model": "gpt-4o-mini"}\n', encoding="utf-8")
    assert load_json(path) == {"model": "gpt-4o-mini"}


def test_load_json_missing(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"
    with pytest.raises(ConfigError, match="config not found"):
        load_json(path)


def test_load_json_invalid(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(ConfigError, match="invalid json"):
        load_json(path)


def test_load_json_root_must_be_object(tmp_path: Path) -> None:
    path = tmp_path / "list.json"
    path.write_text("[1, 2, 3]\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="config root must be an object"):
        load_json(path)


def test_save_json_creates_parent_and_pretty(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "cfg.json"
    save_json(path, {"model": "gpt-4o-mini", "温度": 0.2})
    text = path.read_text(encoding="utf-8")
    assert "gpt-4o-mini" in text
    assert "温度" in text  # ensure_ascii=False
    assert text.endswith("\n")
    assert json.loads(text)["model"] == "gpt-4o-mini"


def test_load_agent_config_defaults(tmp_path: Path) -> None:
    path = tmp_path / "agent.json"
    save_json(path, {"model": "gpt-4o-mini"})
    cfg = load_agent_config(path)
    assert cfg == AgentConfig(model="gpt-4o-mini", temperature=0.2, max_tokens=1024)


def test_load_agent_config_strips_model(tmp_path: Path) -> None:
    path = tmp_path / "agent.json"
    save_json(path, {"model": "  gpt-4o-mini  ", "temperature": 0.5, "max_tokens": 256})
    cfg = load_agent_config(path)
    assert cfg.model == "gpt-4o-mini"
    assert cfg.temperature == 0.5
    assert cfg.max_tokens == 256


def test_load_agent_config_empty_model(tmp_path: Path) -> None:
    path = tmp_path / "agent.json"
    save_json(path, {"model": "   "})
    with pytest.raises(ConfigError, match="model must not be empty"):
        load_agent_config(path)


def test_load_agent_config_temperature_out_of_range(tmp_path: Path) -> None:
    path = tmp_path / "agent.json"
    save_json(path, {"model": "gpt-4o-mini", "temperature": 2.5})
    with pytest.raises(ConfigError, match="temperature out of range"):
        load_agent_config(path)


def test_load_agent_config_bad_max_tokens(tmp_path: Path) -> None:
    path = tmp_path / "agent.json"
    save_json(path, {"model": "gpt-4o-mini", "max_tokens": 0})
    with pytest.raises(ConfigError, match="max_tokens must be >= 1"):
        load_agent_config(path)


def test_save_and_reload_agent_config(tmp_path: Path) -> None:
    path = tmp_path / "out" / "agent.json"
    original = AgentConfig(model="gpt-4o-mini", temperature=0.1, max_tokens=512)
    save_agent_config(path, original)
    assert load_agent_config(path) == original


def test_sample_fixture_loads() -> None:
    sample = Path(__file__).resolve().parent.parent / "fixtures" / "agent.sample.json"
    cfg = load_agent_config(sample)
    assert cfg.model == "gpt-4o-mini"
