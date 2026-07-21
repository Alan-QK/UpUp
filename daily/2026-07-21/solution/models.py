"""参考实现：请先自己完成 exercise/ 再对照。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


@dataclass
class User:
    id: str
    name: str
    role: Role


@dataclass
class AgentConfig:
    model: str
    temperature: float = 0.2
    max_tokens: int = 1024
