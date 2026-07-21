"""Day 2 模型与校验测试。"""

from __future__ import annotations

import pytest

from models import AgentConfig, Role, User
from validate import (
    ConfigError,
    ValidationError,
    build_agent_config,
    create_user,
    describe_user,
)


def test_role_values() -> None:
    assert Role.ADMIN.value == "admin"
    assert Role.USER.value == "user"
    assert Role.GUEST.value == "guest"


def test_create_user_ok() -> None:
    user = create_user("u1", "Ada", Role.ADMIN)
    assert user == User(id="u1", name="Ada", role=Role.ADMIN)


def test_create_user_strips_and_accepts_role_str() -> None:
    user = create_user("  u2 ", "  Alan ", "user")
    assert user.id == "u2"
    assert user.name == "Alan"
    assert user.role is Role.USER


def test_create_user_empty_name_raises() -> None:
    with pytest.raises(ValidationError, match="name must not be empty"):
        create_user("u1", "   ", Role.USER)


def test_create_user_invalid_role_raises() -> None:
    with pytest.raises(ValidationError, match="invalid role"):
        create_user("u1", "Ada", "superuser")


def test_build_agent_config_defaults() -> None:
    cfg = build_agent_config("gpt-4o-mini")
    assert cfg == AgentConfig(model="gpt-4o-mini", temperature=0.2, max_tokens=1024)


def test_build_agent_config_temperature_out_of_range() -> None:
    with pytest.raises(ConfigError, match="temperature out of range"):
        build_agent_config("gpt-4o-mini", temperature=2.5)


def test_build_agent_config_empty_model() -> None:
    with pytest.raises(ConfigError, match="model must not be empty"):
        build_agent_config("  ")


def test_build_agent_config_bad_max_tokens() -> None:
    with pytest.raises(ConfigError, match="max_tokens must be >= 1"):
        build_agent_config("gpt-4o-mini", max_tokens=0)


def test_describe_user() -> None:
    user = User(id="u1", name="Ada", role=Role.ADMIN)
    assert describe_user(user) == "Ada <u1> (admin)"
