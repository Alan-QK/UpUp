"""Day 2 练习：结构化模型定义。

请完成 TODO，使 tests/ 全部通过。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    """用户角色。"""

    # TODO: 定义 ADMIN / USER / GUEST，值分别为 "admin" / "user" / "guest"
    ...


@dataclass
class User:
    """系统用户。"""

    # TODO: 字段 id: str, name: str, role: Role
    ...


@dataclass
class AgentConfig:
    """Agent 运行配置。

    默认值：
    - temperature = 0.2
    - max_tokens = 1024
    """

    # TODO: 字段 model: str, temperature: float = 0.2, max_tokens: int = 1024
    ...
