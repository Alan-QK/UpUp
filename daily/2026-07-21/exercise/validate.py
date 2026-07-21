"""Day 2 练习：校验与工厂函数。

请完成 TODO，使 tests/ 全部通过。
"""

from __future__ import annotations

from models import AgentConfig, Role, User


class ValidationError(ValueError):
    """输入字段不合法。"""


class ConfigError(ValueError):
    """配置不合法。"""


def create_user(user_id: str, name: str, role: Role | str) -> User:
    """创建用户。

    规则：
    - user_id / name 去掉首尾空格后不能为空
      → ValidationError("id must not be empty" / "name must not be empty")
    - role 若是 str，必须能转成 Role；非法值
      → ValidationError("invalid role: {role}")
    - 返回 User(id=cleaned_id, name=cleaned_name, role=Role(...))
    """
    # TODO: 实现这里
    raise NotImplementedError


def build_agent_config(
    model: str,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> AgentConfig:
    """构建并校验 Agent 配置。

    规则：
    - model 去掉首尾空格后不能为空 → ConfigError("model must not be empty")
    - temperature 必须在 [0, 2] → ConfigError("temperature out of range")
    - max_tokens 必须是正整数（>= 1）→ ConfigError("max_tokens must be >= 1")
    """
    # TODO: 实现这里
    raise NotImplementedError


def describe_user(user: User) -> str:
    """返回可读描述：'{name} <{id}> ({role_value})'

    例：User(id='u1', name='Ada', role=Role.ADMIN)
      → "Ada <u1> (admin)"
    """
    # TODO: 实现这里
    raise NotImplementedError
