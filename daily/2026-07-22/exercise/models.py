"""Day 3：Agent 配置模型（已提供，一般无需修改）。"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class AgentConfig:
    """Agent 运行配置。"""

    model: str
    temperature: float = 0.2
    max_tokens: int = 1024

    def to_dict(self) -> dict[str, str | float | int]:
        """转为可 JSON 序列化的 dict。"""
        return asdict(self)
