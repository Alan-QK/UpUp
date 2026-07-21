"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

from models import AgentConfig, Role, User


class ValidationError(ValueError):
    """输入字段不合法。"""


class ConfigError(ValueError):
    """配置不合法。"""


def create_user(user_id: str, name: str, role: Role | str) -> User:
    cleaned_id = user_id.strip()
    cleaned_name = name.strip()
    if not cleaned_id:
        raise ValidationError("id must not be empty")
    if not cleaned_name:
        raise ValidationError("name must not be empty")

    if isinstance(role, Role):
        parsed_role = role
    else:
        try:
            parsed_role = Role(role)
        except ValueError as exc:
            raise ValidationError(f"invalid role: {role}") from exc

    return User(id=cleaned_id, name=cleaned_name, role=parsed_role)


def build_agent_config(
    model: str,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> AgentConfig:
    cleaned_model = model.strip()
    if not cleaned_model:
        raise ConfigError("model must not be empty")
    if not 0 <= temperature <= 2:
        raise ConfigError("temperature out of range")
    if max_tokens < 1:
        raise ConfigError("max_tokens must be >= 1")
    return AgentConfig(
        model=cleaned_model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def describe_user(user: User) -> str:
    return f"{user.name} <{user.id}> ({user.role.value})"
